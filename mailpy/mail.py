"""
mailpy (https://github.com/Y4hL/mailpy)
Python IMAP and SMTP Wrapper

Author: Y4hL (https://github.com/Y4hL)
"""
import email
import imaplib
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate

from .exceptions import *


class Server:
    """ Base Server class """

    def __init__(self, imap_addr: tuple, smtp_addr: tuple) -> None:
        """ Initialize Server """
        self.imap_addr = imap_addr
        self.smtp_addr = smtp_addr

        self.__reset()

    def __reset(self) -> None:
        """ Define/reset variables """
        self.imap = None
        self.loggedin = False
        self.username = None
        self.password = None

        self.mail_ids = []
        self.mailboxes = []
        self.mailbox = None

    def _connect_imap(self) -> None:
        """ Connect to IMAP """
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_addr[0], self.imap_addr[1])
        except Exception as error:
            raise IMAPException(error) from error

    def login(self, username: str, password: str) -> None:
        """ IMAP Login """

        if not self.imap:
            self._connect_imap()

        try:
            response, error = self.imap.login(username, password)
        except Exception as error:
            raise IMAPAuthenticationError(error) from error

        if response != 'OK':
            raise IMAPAuthenticationError(response, error)

        self.username = username
        self.password = password
        self.loggedin = True

    def get_mailboxes(self) -> list:
        """ Get all mailboxes """

        if not self.loggedin:
            raise NotLoggedInError

        try:
            response, mailbox_list = self.imap.list()
        except Exception as error:
            raise IMAPException(error) from error

        if response != 'OK':
            raise IMAPException(response, mailbox_list)

        for mailbox in mailbox_list:
            split_mailbox = mailbox.split(b' "/" ')
            if b'Noselect' in split_mailbox[0]:
                continue
            self.mailboxes.append(split_mailbox[-1])

        return self.mailboxes

    def select_mailbox(self, mailbox: bytes) -> bytes:
        """ Select a mailbox """

        if not self.loggedin:
            raise IMAPAuthenticationError

        try:
            response, number_of_mails = self.imap.select(mailbox)
        except Exception as error:
            raise IMAPException(error) from error

        if response != 'OK':
            raise IMAPException(response, number_of_mails)

        self.mailbox = mailbox
        self.mail_ids = []

        return number_of_mails

    def close_mailbox(self) -> None:
        """ Closes current mailbox """

        if not self.mailbox:
            return

        try:
            response, error = self.imap.close()
        except Exception as error:
            raise IMAPException(error) from error

        if response != 'OK':
            raise IMAPException(response, error)

        self.mailbox = None

    def create_mailbox(self, mailbox: str) -> None:
        """ Create a mailbox """

        if not self.loggedin:
            raise NotLoggedInError

        if mailbox.encode() in self.mailboxes:
            raise MailboxAlreadyExists(mailbox)

        try:
            response, error = self.imap.create(mailbox)
        except Exception as error:
            raise IMAPException(error) from error

        if response != 'OK':
            raise IMAPException(response, error)

        self.mailboxes.append(mailbox.encode())

    def delete_mailbox(self, mailbox: str) -> None:
        """ Delete a mailbox """

        if not self.loggedin:
            raise NotLoggedInError

        if not mailbox.encode() in self.mailboxes:
            raise InvalidMailboxError(mailbox)

        try:
            response, error = self.imap.delete(mailbox)
        except Exception as error:
            raise MailboxException(error) from error

        if response != 'OK':
            raise MailboxException(response, error)

        self.mailboxes.remove(mailbox.encode())

    def get_mail_ids(self) -> list:
        """ Fetch all mail ids in current mailbox """

        if not self.loggedin:
            raise IMAPAuthenticationError

        try:
            response, data = self.imap.search(None, "ALL")
        except Exception as error:
            raise IMAPException(error) from error

        if response != 'OK':
            raise IMAPException(response, data)

        mail_ids = data[0]
        if mail_ids == b'':
            self.mail_ids = []
        else:
            self.mail_ids = mail_ids.split(b' ')

        return self.mail_ids

    def get_mail(self, mail_id: bytes) -> email.message.Message:
        """ Fetch a mail by mail id """

        if not self.loggedin:
            raise NotLoggedInError

        if not mail_id in self.mail_ids:
            raise InvalidMailID(mail_id)

        try:
            response, mail_data = self.imap.fetch(mail_id, '(RFC822)')
        except Exception as error:
            raise IMAPException(error) from error

        if response != 'OK':
            raise IMAPException(response, mail_data)

        message = email.message_from_bytes(mail_data[0][1])

        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                message['Body'] = part.get_payload(decode=True)

        return message

    def get_latest_mails(self, amount: int, start: int = 0) -> email.message.Message:
        """ Generator for returning x amount of latest mails """

        if not self.loggedin:
            raise IMAPAuthenticationError

        if start >= len(self.mail_ids):
            return

        if amount + start > len(self.mail_ids):
            amount = len(self.mail_ids) - start

        # Get x amount of latest mail
        mail_ids = self.mail_ids[-(amount + start)::]
        # Reverse the list so newest mail comes first
        mail_ids.reverse()
        # Remove start amount of mail
        mail_ids = mail_ids[start::]

        for mail_id in mail_ids:
            yield self.get_mail(mail_id)

    def search(self, query: str) -> list:
        """ Search mails by query """

        if not self.loggedin:
            raise NotLoggedInError

        # Replace double quotes from query
        query = query.replace('"', '')
        parts = ['FROM', 'SUBJECT', 'BODY']
        matched_ids = []

        for part in parts:
            search = f'{part} "{query}"'

            try:
                response, data = self.imap.search('UTF-8', search.encode())
            except Exception as error:
                raise IMAPException(error) from error

            if response != 'OK':
                raise IMAPException(response, data)

            if data[0] == b'':
                continue

            matched_ids.extend(data[0].split(b' '))

        # Remove duplicates
        mail_ids = list(set(matched_ids))
        mail_ids.sort(reverse=True)

        return mail_ids

    def attachments(self, message: email.message.Message) -> list:
        """ Check for attachments in a message object """

        files = []
        for part in message.walk():
            if part.get_content_maintype() == 'multitype':
                continue
            if part.get_content_disposition() is None:
                continue
            filename = part.get_filename()
            if filename:
                files.append(filename)

        return files

    def get_attachment(self, message: email.message.Message, attachment_name: str) -> bytes:
        """ Retreive attachment data from message """

        for part in message.walk():
            if part.get_content_maintype() == 'multitype':
                continue
            if part.get_content_disposition() is None:
                continue
            if part.get_filename() != attachment_name:
                continue

            return part.get_payload(decode=True)
        raise InvalidAttachmentName(attachment_name)

    def delete(self, mail_ids: list) -> None:
        """ Delete a single or multiple mails """

        if not self.loggedin:
            raise NotLoggedInError

        # Sort and reverse to prevent mail ids from changing after each deletion
        mail_ids.sort(reverse=True)

        errors = []
        for mail_id in mail_ids:
            if mail_id not in self.mail_ids:
                errors.append(InvalidMailID(mail_id))
            try:
                response, error = self.imap.store(mail_id, '+FLAGS', '\\Deleted')
            except Exception as error:
                errors.append(IMAPException(error))
                continue

            if response != 'OK':
                errors.append(IMAPException(response, error))
                continue

            self.mail_ids.pop()

        try:
            response, error = self.imap.expunge()
        except Exception as error:
            raise IMAPException(error) from error

        if response != 'OK':
            errors.append(IMAPException(response, error))

        if errors:
            raise IMAPException(errors)

    def logout(self) -> None:
        """ IMAP Log out """

        if self.mailbox:
            self.close_mailbox()
        if self.imap:
            self.imap.logout()
        self.__reset()

    def send(self, recipients: list, subject: str, body: str, attachments: list = None, display_name: str = False) -> None:
        """ Send mail using SMTP """

        if self.username is None or self.password is None:
            raise SMTPAuthenticationError

        message = MIMEMultipart()
        message['From'] = formataddr((display_name, self.username))
        message['Subject'] = subject

        message.attach(MIMEText(body))

        if attachments:
            for attachment in attachments:
                if not os.path.isfile(attachment):
                    raise InvalidAttachmentError(attachment)
                filename = os.path.basename(attachment)
                with open(attachment, 'rb') as file:
                    part = MIMEApplication(file.read())
                part.add_header('Content-Disposition', 'attachment', filename=filename)
                message.attach(part)

        with smtplib.SMTP_SSL(self.smtp_addr[0], self.smtp_addr[1]) as smtp:
            smtp.login(self.username, self.password)

            for recipient in recipients:
                message['To'] = recipient
                message['Date'] = formatdate(localtime=True)
                smtp.sendmail(self.username, recipient, message.as_string())

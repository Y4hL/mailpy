""" mailpy package exceptions """


class IMAPException(RuntimeError):
    """ Base IMAP Exception """


class IMAPAuthenticationError(IMAPException):
    """ IMAP Authentication Error """


class NotLoggedInError(IMAPAuthenticationError):
    """ Not Logged In Error """


class InvalidMailID(IMAPException):
    """ Invalid Mail ID """


class InvalidAttachmentName(IMAPException):
    """ Invalid Attachment Name """


class MailboxException(IMAPException):
    """ Base Mailbox Exception """


class InvalidMailboxError(IMAPException):
    """ Invalid Mailbox  """


class MailboxAlreadyExists(IMAPException):
    """ Mailbox already exists """



class SMTPException(RuntimeError):
    """ Base SMTP Exception """


class SMTPAuthenticationError(SMTPException):
    """ SMTP Authentication Error """


class InvalidAttachmentError(SMTPException):
    """ Invalid Attachment Error """

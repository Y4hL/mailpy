"""
Command Line Interface for the mailpy package
"""
import getpass
import os
import platform

import mailpy


def cli() -> None:
    """ mailpy Command-line Interface """

    if platform.system() == 'Windows':
        os.system(f'title mailpy - v{mailpy.__version__}')

    mailpy_logo = f"""
                        _ __           
       ____ ___  ____ _(_) /___  __  __
      / __ `__ \/ __ `/ / / __ \/ / / /
     / / / / / / /_/ / / / /_/ / /_/ / 
    /_/ /_/ /_/\__,_/_/_/ .___/\__, /  
                       /_/    /____/   
                v{mailpy.__version__}"""

    print(mailpy_logo)

    if not input('Use default gmail addresses and ports? (yes/no)') == 'yes':
        imap_addr = (input('IMAP Address: '), int(input('IMAP Port: ')))
        smtp_addr = (input('SMTP Address: '), int(input('SMTP Port: ')))
    else:
        imap_addr = ('imap.gmail.com', 993)
        smtp_addr = ('smtp.gmail.com', 465)
        print('Defaulting to Gmail Config')

    server = mailpy.Server(imap_addr, smtp_addr)

    while not server.loggedin:
        email = input('Username: ')
        password = getpass.getpass()

        try:
            server.login(email, password)
        except Exception:
            continue

    print('Login Successful!')

    server.select_mailbox(b'INBOX')
    server.get_mail_ids()

    for mail in server.get_last_mails(20):

        if not mail:
            break

        print(f"From: {mail['From']}\n" \
            f"Date: {mail['Date']}\n" \
            f"Subject: {mail['Subject']}\n" \
            f"Body:\n{mail['Body']}\n\n"
        )
        attachments = server.attachments(mail)
        if attachments:
            print('Attachments: ', end='')
            for attachment in attachments:
                print(attachment, end='')



if __name__ == '__main__':
    cli()

# mailpy  

Python IMAP and SMTP Wrapper  
  
## Setup  
  
To use mailpy with Gmail you will need to create a [App Password](https://myaccount.google.com/apppasswords) for your Google Account  
  
## Installation  
  
```bash  
python3 -m pip install mailpy  
```  
or  
```bash  
git clone https://github.com/Y4hL/mailpy.git && python3 setup.py install  
```  
  
## Usage  
  
```python
import mailpy

# Example with GMail
IMAP_ADDRESS = ('imap.google.com', 993)
SMTP_ADDRESS = ('smtp.google.com', 465)
server = mailpy.Server(IMAP_ADDRESS, SMTP_ADDRESS)
server.login('username', 'password')
server.select_mailbox('INBOX')
for mail_id in server.get_mail_ids():
    mail = server.get_mail(mail_id)
    print(mail['Subject'])
```  
  
## Contributing  
  
Before creating an issue, please ensure that it hasn't already been reported/suggested.  
See [the contribution guide](https://github.com/Y4hL/mailpy/blob/master/CONTRIBUTING.md) if you'd like to submit a PR.  
  
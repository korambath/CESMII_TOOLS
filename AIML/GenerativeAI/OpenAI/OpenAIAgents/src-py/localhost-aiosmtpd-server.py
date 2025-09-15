import asyncio
from aiosmtpd.controller import Controller

class CustomSMTPHandler:
    async def handle_DATA(self, server, session, envelope):
        print('Message from %s' % envelope.mail_from)
        print('Message to %s' % envelope.rcpt_tos)
        
        # Access the message content
        message_content = envelope.content.decode('utf-8', errors='replace')
        
        print('Message content (raw):')
        print('---BEGIN MESSAGE---')
        print(message_content)
        print('---END MESSAGE---')
        
        # You can use the email library to parse the message
        # For a more structured approach, you might do this:
        from email import message_from_string
        msg = message_from_string(message_content)
        
        print('\nMessage content (parsed):')
        print('Subject:', msg['subject'])
        print('Body:')
        
        # This part handles multi-part messages
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                
                # We're interested in the plain text part of the body
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    print(body)
                    break # Exit after finding the first plain text part
        else:
            # Handle a simple single-part message
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            print(body)

        return '250 OK'

async def amain():
    handler = CustomSMTPHandler()
    controller = Controller(handler, hostname='127.0.0.1', port=8025)
    controller.start()
    print("SMTP server started on 127.0.0.1:8025")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        print("SMTP server stopped.")

if __name__ == '__main__':
    asyncio.run(amain())

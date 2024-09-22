import imaplib
import email
from email.header import decode_header
import os
import sys
import smtplib
from email.message import EmailMessage
from email.header import make_header
import pandas as pd
import numpy as np
import io

from Code.Functions.vat_checker import run_vat_checker

    
def login(EMAIL_ACCOUNT, EMAIL_PASSWORD):

    # Connect to the IMAP server
    imap_server = imaplib.IMAP4_SSL("imap.gmail.com")
    imap_server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    imap_server.select("INBOX")

    return imap_server


def logout(imap_server):
    imap_server.close()
    imap_server.logout()


def process_file(filepath):
    # Example processing function
    try:
        with open(filepath, "r") as file:
            content = file.read()

        processed_content = content.upper()
        processed_filepath = filepath.replace("attachments", "processed")
        os.makedirs(os.path.dirname(processed_filepath), exist_ok=True)
        with open(processed_filepath, "w") as file:
            file.write(processed_content)
        return processed_filepath
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def send_email(to_email, subject, body, EMAIL_ACCOUNT, EMAIL_PASSWORD, attachment_path=None, attachment=None, filename="output.xlsx"):
    """
    Sends an email with an optional attachment.

    Parameters:
        to_email (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Body text of the email.
        attachment_path (str, optional): File path of the attachment to send.
        attachment (pd.DataFrame, optional): DataFrame to send as an attachment.
        filename (str, optional): Filename for the attachment.

    Returns:
        None
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ACCOUNT
    msg["To"] = to_email
    msg.set_content(body)
    
    if attachment_path:
        # Attach file from disk
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="octet-stream",
            filename=file_name
        )
    elif attachment is not None:
        if isinstance(attachment, pd.DataFrame):
            if filename.endswith('.xlsx'):
                # Write DataFrame to Excel format in memory
                with io.BytesIO() as output:
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        attachment.to_excel(writer, index=False, sheet_name="Checked VAT Numbers")
                    data = output.getvalue()
                msg.add_attachment(
                    data,
                    maintype="application",
                    subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename=f'output_{filename}'
                )
            elif filename.endswith('.csv'):
                # Write DataFrame to CSV format in memory
                csv_data = attachment.to_csv(index=False).encode('utf-8')
                msg.add_attachment(
                    csv_data,
                    maintype="text",
                    subtype="csv",
                    filename=f'output_{filename}'
                )
            else:
                print("Unsupported file format for attachment. Please use '.xlsx' or '.csv'.")
        else:
            print("Attachment not in a valid format, please provide a pandas DataFrame.")
    else:
        print("No attachment to send.")
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print(f"Email sent to {to_email}")


def read_email(imap_server, EMAIL_ACCOUNT, EMAIL_PASSWORD):
    # Search for all emails in the inbox
    status, messages = imap_server.search(None, "UNSEEN")
    email_ids = messages[0].split()

    for email_id in email_ids:
        res, msg = imap_server.fetch(email_id, "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                subject = str(make_header(decode_header(msg["Subject"])))
                print(f"Processing email with subject: {subject}")
                from_ = msg.get("From")
                sender_email = email.utils.parseaddr(from_)[1]

                from_ = msg.get("From")
                sender_name, sender_email = email.utils.parseaddr(from_)

                # Handle cases where sender's name is missing
                if not sender_name:
                    sender_name = sender_email.split('@')[0].replace('.', ' ').title()

                # Process only if the email has a specific subject
                if "btw lijst" in subject.lower() or 'vat lijst' in subject.lower() or 'vat list' in subject.lower() or 'btw list' in subject.lower():
                    input_file = None  # Initialize input_file
                    if msg.is_multipart():
                        for part in msg.walk():
                            filename = part.get_filename()
                            content_disposition = part.get_content_disposition()
                            if content_disposition == 'attachment' and filename:
                                print(f'Processing attachment: {filename}')

                                attachment_data = part.get_payload(decode=True)
                                if ".csv" in filename.lower():
                                    # For CSV files
                                    try:
                                        csv_data = attachment_data.decode('utf-8')
                                        input_file = pd.read_csv(io.StringIO(csv_data))
                                    except Exception as e:
                                        print(f"Error reading CSV: {e}")
                                        continue
                                elif ".xlsx" in filename.lower():
                                    # For Excel files
                                    try:
                                        input_file = pd.read_excel(io.BytesIO(attachment_data))
                                    except Exception as e:
                                        print(f"Error reading Excel file: {e}")
                                        continue
                                else:
                                    print(f"Unsupported file type: {filename}")
                                    continue  # Skip unsupported file types

                                # Process the file if successfully read
                                if input_file is not None:
                                    output_file = run_vat_checker(input_file)

                                    # Send the processed file back
                                    message = f"""Hi {sender_name}, 
                                            
                                    please find the attached file with the VAT numbers checked.
                                    
                                    Kind regards, 
                                    Data Wolf Team"""

                                    send_email(
                                        to_email=sender_email,
                                        subject=f"VAT Numbers Checked for {part.get_filename()}",
                                        body=message,
                                        attachment=output_file,  # Assuming send_email can handle a DataFrame
                                        filename=part.get_filename(),
                                        EMAIL_ACCOUNT=EMAIL_ACCOUNT,
                                        EMAIL_PASSWORD=EMAIL_PASSWORD
                                    )
                    else:
                        print("Email is not multipart; no attachments found.")

                elif 'stink ik' in subject.lower():
                    random_value = np.random.randint(0, 2)
                    if random_value == 0:
                        output = "Ja, je stinkt."
                    else:
                        output = "Nee, je stinkt niet."

                    message = f"""Hi {sender_name}, 
                                        
                    Na grondig onderzoek van alle bestanden die in de bijlage zaten, of door naar de naam van je email te bekijken zijn we er over uit.

                    {output}

                    Met vriendelijke groet, 
                    Data Wolf Team"""
                    
                    send_email(
                            to_email=sender_email,
                            subject=f"Antwoord op: {subject}",
                            body=message,
                            EMAIL_ACCOUNT=EMAIL_ACCOUNT,
                            EMAIL_PASSWORD=EMAIL_PASSWORD
                        )


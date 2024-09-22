from dotenv import load_dotenv
import os
from Code.check_email import login, read_email, logout

def main():

    # Load variables from credentials.env
    load_dotenv('credentials.env')

    # Retrieve the environment variables
    EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    imap_server = login(EMAIL_ACCOUNT=EMAIL_ACCOUNT, EMAIL_PASSWORD=EMAIL_PASSWORD)
    read_email(imap_server, EMAIL_ACCOUNT=EMAIL_ACCOUNT, EMAIL_PASSWORD=EMAIL_PASSWORD)
    logout(imap_server)

if __name__ == "__main__":
    main()

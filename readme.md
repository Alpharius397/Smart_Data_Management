How to run this project:

    1) Install Docker
    2) Define the .env file using the env.template file
    3) Define the .env.prod file using the env.prod.template file
    4) Change the SSL certificates inside nginx/certificate
    5) Change the PDF certificates inside signature/certificate

How to generate SSL Certificate (Self Signed):
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/certificate/key.key -out nginx/certificate/cert.crt

How to generate PDF Certificate (Self Signed):

    openssl req -x509 -newkey rsa:4096 -keyout signature/key.pem -out signature/cert.pem -sha256 -days 365

Docker Command:

    docker compose up --build
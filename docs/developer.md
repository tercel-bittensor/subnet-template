# Issue with btcli subnets show --netuid Command and raw.githubusercontent.com
Fail to run btcli subnets show --netuid 2 --network local --verbose

## Preparation
Modify /etc/hosts
```sh
$ sudo echo "127.0.0.0 raw.githubusercontent.com >> /etc/hosts
```

Generate certificates in the nginx directory at the same level as the current project
```sh
cd ../nginx
```

## Generate a Self-signed CA and Use It to Sign the Server Certificate
1. Generate a CA certificate with key usage extension
Step 1: Create an openssl configuration file (e.g., ca.cnf)
```sh
[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
x509_extensions    = v3_ca
prompt             = no

[ req_distinguished_name ]
C  = CN
ST = Test
L  = Test
O  = Test
OU = Test
CN = MyTestCA

[ v3_ca ]
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer:always
basicConstraints = critical,CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
```

Step 2: Generate a new CA certificate
```sh
openssl req -x509 -newkey rsa:2048 -days 3650 -keyout ca.key -out ca.crt -config ca.cnf
```
## Generate a Server Certificate with SAN
1. Create an openssl configuration file server.cnf
```sh
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = req_ext

[ dn ]
C  = CN
ST = Test
L  = Test
O  = Test
OU = Test
CN = raw.githubusercontent.com

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = raw.githubusercontent.com
IP.1 = 127.0.0.1
```

2. Generate the server private key and CSR
```sh
openssl genrsa -out nginx.key 2048
openssl req -new -key nginx.key -out nginx.csr -config server.cnf
```

3. Use the CA to sign the server certificate (with SAN)
```sh
openssl x509 -req -in nginx.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out nginx.crt -days 3650 -sha256 -extfile server.cnf -extensions req_ext
```

4. Merge fullchain.crt and configure nginx
```sh
  cat nginx.crt ca.crt > fullchain.crt
```

5. Configure nginx to use the newly generated fullchain.crt and nginx.key
```sh
cat fullchain.crt > /opt/homebrew/etc/nginx/ssl/nginx.crt
cat nginx.key > /opt/homebrew/etc/nginx/ssl/nginx.key

brew services restart nginx 

cat /opt/homebrew/var/log/nginx/error.log 
```

## Run btcli subnets show --netuid
Enter the current project directory
1. Append ca.crt to Python certifi's CA file (only needs to be done once)
```sh
cat ../nginx/ca.crt >> $(python -m certifi)
```

8. Run btcli
```sh
$ btcli subnets show --netuid 2 --network local --verbose
# Error: ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate

# Sometimes aiohttp/ssl only recognizes SSL_CERT_FILE, you can:

$ export SSL_CERT_FILE=$(python -m certifi)
# It is recommended to run echo 'export SSL_CERT_FILE=$(python -m certifi)' >> ./venv/bin/activate

$ btcli subnets show --netuid 2 --network local --verbose
```

9. Trust the certificate in your browser
```sh
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ca.crt

# You may need to manually right-click "Show Info" -> "Trust" and select Always Trust
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain fullchain.crt

curl -v https://raw.githubusercontent.com
```

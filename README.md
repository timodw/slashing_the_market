# slashing_the_market

This is a slack integrations that provides stock related commands

 - /stock TSLA 
    - shows the current TSLA stock price
- /graph TSLA
   - shows a graph with the TSLA stock price history
   
# development/testing

```
git clone https://github.com/JensTimmerman/slashing_the_market.git
cd slashing_the_market
pip3 install -r requirements.txt
python3 stocks.py
```
```
echo -n text=TSLA| POST http://127.0.0.1:8080/stock -E
echo -n text=EUR/USD| POST http://127.0.0.1:8080/stock -E
```

# installation

install using a real webserver

on your stocks host
```
adduser stocks
cp stocks.service /etc/systemd/system/
mv slashing_the_market /home/stocks/
dnf install gcc python-devel
pip3 install wheel uwsgi
service stocks enable
service stocks start
```
on your nginx webproxy
```


vim /etc/nginx/sites-available/stocks
server {
    listen 80;
    server_name stocks.your_domain;
    location / {
        include uwsgi_params;
        # use this if you run on same machine (also edit socks.ini )
        #uwsgi_pass unix:/home/stocks/slashing_the_market/stocks.sock;
          proxy_pass http://192.168.1.106:8080;
          proxy_redirect off ;
          proxy_set_header Host $host ;
          proxy_set_header X-Real-IP $remote_addr ;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for ;
          proxy_max_temp_file_size 0 ; 
          client_max_body_size 10m ;
          client_body_buffer_size 128k ;
          proxy_connect_timeout 90 ;
          proxy_send_timeout 90 ;
          proxy_read_timeout 90 ;
          proxy_buffer_size 4k ;
          proxy_buffers 4 32k ;
          proxy_busy_buffers_size 64k ;
          proxy_temp_file_write_size 64k ;
     }
}

ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled
nginx -t
systemctl restart nginx
pip3 install certbot-nginx
certbot --nginx -d yourodmain -d www.yourodmain -d stocks.yourdomain --hsts --staple-ocsp --uir
```

let certbot renew your certs daily
crontab -e
  - `18 6 * * * certbot renew --post-hook "systemctl reload nginx"`



browse to http://stocks.your_domain

DNS: 
Don't forget to set a CAA DSN record : @ CAA 0 issue "letsencrypt.org"
And enable DNSSec

# maintenance

- Regularly check this repo for fixes
- run a cron job that updates your pip dependencies 
  - crontab -e 
    - `0 8 * * * pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip3 install -U`

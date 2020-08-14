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
echo TSLA| POST http://127.0.0.1:8080/stock -E
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
        #uwsgi_pass unix:/home/sammy/myproject/myproject.sock;
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

```
browse to http://stocks.your_domain

# maintenance

Regularly check this repo for fixes
run a cron job that updates your pip dependencies 
 - crontab -e 
    - `0 8 * * * pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip3 install -U`

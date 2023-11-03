cd ..\frontend\wom-miner-frontend
call npm install
call npm run build
ssh pg-wom "rm -r /var/www/wom/htdocs/frontend"
scp -r dist pg-wom:/var/www/wom/htdocs/frontend
PAUSE
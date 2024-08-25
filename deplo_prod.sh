sshpass -p uYx_7gQVEVu^r- ssh root@91.222.237.142

cd /home/platform
git pull
docker-compose -f docker-compose.prod.yml up -d
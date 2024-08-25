sshpass -p mT4wvmMNzFX.@8 ssh root@81.200.153.167 << EOF
    cd /home/platform
    source ./envs/test.env
    #bash prefill.sh
    git pull
    ssh-add -l
    docker-compose -f docker-compose.test.yml up -d
EOF


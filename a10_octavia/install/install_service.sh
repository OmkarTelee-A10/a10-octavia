#!/bin/bash

if [ "$EUID" -ne 0 ]
    then echo "Please run as root"
    exit
fi


SYSTEMD_SCRIPT_DIR=$(cd $(dirname ${BASH_SOURCE:=$0}) && pwd)
CONTROLLER="a10-controller-worker.service"
HOUSEKEEPER="a10-house-keeper.service"
HEALTHMANAGER="a10-health-manager.service"

SERVICES=("$CONTROLLER" "$HOUSEKEEPER" "$HEALTHMANAGER")

echo "[+] Installing a10-controller-worker"
echo "[+] Installing a10-house-keeper"
echo "[+] Installing a10-health-manager"

for i in ${SERVICES[@]}; do
	cp -f "$SYSTEMD_SCRIPT_DIR/${i}" /etc/systemd/system/
	chown root:root /etc/systemd/system/${i}
done

echo "[=] Reloading systemd" 
systemctl daemon-reload

for j in ${SERVICES[@]}; do
	echo "[=] Enabling ${j}"
        systemctl enable ${j}
        echo "[=] Starting ${j}"
        systemctl start ${j}
done

echo "Completed installation a10-controller-worker, a10-house-keeper and a10-health-manager service"

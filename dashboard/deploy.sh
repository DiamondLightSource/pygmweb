git pull
kubectl cp ./landing_pages/* pgmtool-nginx-deployment-785fb44df8-ft9wb:/usr/share/nginx/html
kubectl cp ./site/* pgmtool-nginx-deployment-785fb44df8-ft9wb:/usr/share/nginx/html/app

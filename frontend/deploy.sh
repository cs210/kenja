npm run build
cp -r build/* /usr/share/nginx/html/
systemctl restart nginx
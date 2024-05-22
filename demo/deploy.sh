npm run build
cp -r build/* /usr/share/nginx/landing/demo/
systemctl restart nginx

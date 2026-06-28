FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Create non-root user and set up directories
RUN addgroup -g 1001 -S nginxuser && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginxuser nginxuser && \
    mkdir -p /var/cache/nginx /var/log/nginx /tmp && \
    chown -R nginxuser:nginxuser /var/cache/nginx /var/log/nginx /tmp && \
    chmod -R 755 /var/cache/nginx /var/log/nginx

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Use non-root user
USER nginxuser

EXPOSE 8080 8443

CMD ["nginx", "-g", "daemon off;"]

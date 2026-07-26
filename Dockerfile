# Uebergangsseite tierbestattung-memoria.de
#
# Reine statische Seite (HTML + CSS + minimales JS). Das Kontaktformular laeuft
# ueber FormSubmit.co, es wird also kein PHP und kein Mailserver gebraucht.
#
# Deployment ueber Dokploy: Build Type "Dockerfile", Port 80.
#
# Ausgeliefert wird ausschliesslich der Inhalt von public/. Der Wix-Mirror
# (miror-alt/) und die Hilfsskripte (tools/) bleiben ausserhalb des Images.

FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY public/ /usr/share/nginx/html/

EXPOSE 80

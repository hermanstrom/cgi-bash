#!/bin/bash
#
# To encode the binary file, run this command in the directory where it's located.
# 	$ compress < binary | base64
#

# Variables and functions
export PATH=/bin:/usr/bin; DBNAME=cgibash; TABLE=(user path node session); 
declare -A COLUMN=([${TABLE[0]}]='uid uname geos email passwd' [${TABLE[1]}]='vhost fpath nodeid'\
 [${TABLE[2]}]='nodeid type coding data revise ctime uids' [${TABLE[3]}]='sid ctime uid');
decode() { printf '%b' "${1//%/\\x}"; }
encode() { for ((p=0; p<${#1}; p++)); do c=${1:$p:1}; case "${c}" in
 [-_.~a-zA-Z0-9]) echo -n "${c}";; *) printf '%%%02x' "'${c}"; esac; done; }
expire() { date --utc --date=${1:-now} "+%a, %d-%b-%y %H:%M:%S GMT"; }
sessid() { md5sum <<< "$(date +%s)" | awk '{print $1}'; }
form_p() { sed 's/^/[/; s/=/]="/g; s/\&/" [/g; s/$/"/' <<< "${1}"; }
fkey_p() { sed 's/^/"/; s/=[^&]*&/" "/g; s/=.*$/"/' <<< "${1}"; }
cook_p() { sed 's/^/[/; s/=/]="/g; s/; /" [/g; s/$/"/' <<< "${1}"; }
ckey_p() { sed 's/^/"/; s/=[^;]*; /" "/g; s/=.*$/"/' <<< "${1}"; }
authen() { [[ ${#COOKIE[@]} -gt 0 ]] && echo -ne "<form method=post><table style=\"float:right;\"><tr><td style=\"text-align:left;font-family:verdana;font-size:12px\">${COOKIE[name]}</td><td><input type=\"submit\" name=\"submit\" value=\"Logout\"></td></tr></table></form>";
 [[ ${#COOKIE[@]} -eq 0 ]] && echo -ne "<form method=post><table style=\"float:right;\"><tr><td style=\"text-align:left;font-family:verdana;font-size:8px\">User Name</td><td style=\"text-align:left; font-family:verdana; font-size:8px\">Password</td><td></td></tr>"\
"<tr><td><input type=\"text\" size=\"15\" name=\"username\"></td><td><input type=\"password\" size=\"15\" name=\"password\"></td><td><input type=\"submit\" name=\"submit\" value=\"Login\"></td></tr>"\
"$([[ -n ${FORM[message]} ]] && echo -ne "<tr><td colspan=3 style=\"text-align:left;font-family:verdana;font-size:14px;color:red;\">${FORM[message]}</td></tr>";)</table></form>"; }
dbauth() { [[ -z ${1} ]] && return 1; mysql -N -B -e "SELECT PASSWORD('${1}');"; return 0; }; 
dbuser() { [[ -z ${1} ]] && return 1;
 [[ $(mysql -N -B -e "SELECT * FROM ${DBNAME}.${TABLE[0]} WHERE uname='${1}';" | wc -l) -eq 0 ]] && return 2;
 ARRAY=$(for column in ${COLUMN[${TABLE[0]}]}; do echo -n "[${column}]='$(mysql -N -B -e "SELECT ${column} FROM ${DBNAME}.${TABLE[0]} WHERE uname='${1}';")' "; done);
 echo -n "${ARRAY% }"; return 0; };

# DataBase schema auto create
for QUERY in "CREATE DATABASE IF NOT EXISTS ${DBNAME} CHARACTER SET utf8;"\
 "CREATE TABLE IF NOT EXISTS ${DBNAME}.${TABLE[0]} (uid BIGINT UNSIGNED AUTO_INCREMENT, uname VARCHAR(24), geos VARCHAR(64), email VARCHAR(64), passwd VARCHAR(48), PRIMARY KEY (uname), INDEX uname (uid)) TYPE=innodb DEFAULT CHARSET=utf8;"\
 "CREATE TABLE IF NOT EXISTS ${DBNAME}.${TABLE[1]} (vhost VARCHAR(64), fpath VARCHAR(64), nodeid VARCHAR(144), PRIMARY KEY (vhost, fpath), INDEX nodeid (nodeid)) TYPE=innodb DEFAULT CHARSET=utf8;"\
 "CREATE TABLE IF NOT EXISTS ${DBNAME}.${TABLE[2]} (nodeid VARCHAR(144), type VARCHAR(24), coding VARCHAR(24), data LONGBLOB, revise VARCHAR(144), ctime BIGINT UNSIGNED, uids LONGTEXT, PRIMARY KEY (nodeid), INDEX revise (revise), INDEX ctime (ctime)) TYPE=innodb DEFAULT CHARSET=utf8;"\
 "CREATE TABLE IF NOT EXISTS ${DBNAME}.${TABLE[3]} (sid VARCHAR(42), ctime BIGINT UNSIGNED, uid BIGINT UNSIGNED, PRIMARY KEY (sid), INDEX ctime (ctime), INDEX uid (uid)) TYPE=innodb DEFAULT CHARSET=utf8;"\
 "INSERT IGNORE INTO ${DBNAME}.${TABLE[0]} (uid, uname, geos, email, passwd) VALUES (NULL, 'admin', 'Administrator', 'root@localhost', PASSWORD('password'));";
 do mysql -e "${QUERY}"; done;

# Import FORM and COOKES
[[ "${REQUEST_METHOD}" = "POST" ]] && read QUERY_STRING ;
[[ -z ${QUERY_STRING} ]] || eval $(echo -n "declare -A FORM=($(decode "$(form_p "${QUERY_STRING}")")); FORMKEY=($(fkey_p "${QUERY_STRING}"))");
[[ -z ${HTTP_COOKIE} ]] || eval $(echo -n "declare -A COOKIE=($(decode "$(cook_p "${HTTP_COOKIE}")")); COOKIEKEY=($(ckey_p "${HTTP_COOKIE}"))");

# Process FORM responses
case ${FORM[submit]} in 
 Login) if [[ -n ${FORM[username]} ]] && PASSWD=$(dbauth "${FORM[password]}"); then
   if EVAL=$(dbuser "${FORM[username]}"); then eval $(echo "declare -A ROW=(${EVAL}); ROWKEY=(${COLUMN[${TABLE[0]}]});");
    if [[ ${ROW[${ROWKEY[4]}]} == ${PASSWD} ]]; then
     echo -ne "Set-Cookie: sid=$(sessid); expires=$(expire '30min')\nSet-Cookie: name=$(encode "${ROW[${ROWKEY[2]}]}"); expires=$(expire '30min')\nLocation: http://${SERVER_NAME}${SCRIPT_NAME}\n\n";
    else FORM[message]='Password incorrect!'; fi; 
   else FORM[message]='Username incorrect!'; fi; fi;;
 Logout) echo -ne "Set-Cookie: sid=; expires=$(expire '-5min')\nSet-Cookie: name=; expires=$(expire '-5min')\nLocation: http://${SERVER_NAME}${SCRIPT_NAME}\n\n";; esac;

# Process web space
case ${PATH_INFO} in 
 /favicon.ico) echo -ne "Content-Type: image/x-icon\n\n"; base64 -d <<< '
H52QAAAEEAgAgsGACFEMBGAhIUIICEEgHEgAocWLFyFijBOHEIB8IAGsGwkgVKhRAJo0oQLg2bNmAgM4ivkKIbaYYgAoUJACoTKEzC7+G3rRnVGjHo4qraH0
aAsfSsNBG0eKiDsRRquUa9VtSrRyRAAQ4NoqCo1Ld+7YaaUNxh5czJgh06ONDbJFu/ImO4XsUBpeu5gl4nVIUzbAt9TgypUKzTJcarqlyoSLUeBO3bpt02WJ
2SGu3bLZ2mPLVjdtp/Es06SpWyuMsGPLnk27NgA=' | zcat;;
 /logo.png) echo -ne "Content-Type: image/png\n\n"; base64 -d <<< '
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
8Mg0AAEhMAz/IA/NwAk/kQRF4ARE4ApCAAaCAA==' | zcat;;
*) echo -ne "Content-Type: text/html\n\n<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">\n"\
"<html><head>\n<title>Environment</title>\n<link rel=\"icon\" href=\"http://${SERVER_NAME}${SCRIPT_NAME}/favicon.ico\">\n"\
"<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\"></head><body>\n"\
"<table><tr><th><img src=\"http://${SERVER_NAME}${SCRIPT_NAME}/logo.png\"></th><th>$(authen)</th></tr>\n"\
"<tr><td></td><td><pre>$(env)</pre>\n$([[ ${#FORM[@]} -gt 0 ]] && echo -ne "<pre>$(for k in ${FORMKEY[@]} ; do echo -n "FORM[${k}]=\"${FORM[$k]}\"; "; done; echo -ne "\n\"$(dbuser "${FORM[username]}";)\"; \"$(dbauth "${FORM[password]}";)\";\n")</pre>";)"\
"$([[ ${#COOKIE[@]} -gt 0 ]] && echo -ne "<pre>$(for k in ${COOKIEKEY[@]}; do echo -n "COOKIE[${k}]=\"${COOKIE[$k]}\"; "; done)</pre>";)"\
"</td></tr></table></body></html>";; esac;

exit 0;

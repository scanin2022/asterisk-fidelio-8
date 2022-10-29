#!/bin/bash
mysql --batch --silent -ufreepbxuser -p9bddf9b6fcfa -Dasterisk <<<"UPDATE asterisk.billing_extensions SET permission_id=$2 WHERE billing_extensions.sip_num =$1 LIMIT 1;"

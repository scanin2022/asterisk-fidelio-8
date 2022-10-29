#!/bin/bash
mysql --batch --silent -ufreepbxuser -yourpassword -Dasterisk <<<"UPDATE asterisk.billing_extensions SET permission_id=$2 WHERE billing_extensions.sip_num =$1 LIMIT 1;"

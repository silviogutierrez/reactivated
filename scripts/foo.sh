#!/bin/bash

function disable_checks() {
   FOO=$(curl https://www.google.com)
   echo $FOO;
}

function enable_checks() {
    echo "ok";
}


EXISTING=$(disable_checks);
enable_checks "$EXISTING";

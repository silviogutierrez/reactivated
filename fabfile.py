from fabric.api import env

env.sites = {
    'stage': (('silviogutierrez@node.silviogutierrez.com',), '/home/silviogutierrez/www/node.silviogutierrez.com'),
}

from deploy import *

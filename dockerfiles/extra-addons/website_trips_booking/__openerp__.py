# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2015 Acespritech Solutions Pvt. Ltd.
#
##############################################################################
{
    "name" : "Website Trips Booking",
    'summary' : "",
    "version" : "1.0",
    "description": """
        This module helps to create trips from website.
    """,
    'author' : 'Acespritech Solutions Pvt. Ltd.',
    'category' : 'Website',
    'website' : 'http://acespritech.com',
    'price': 00, 
    'currency': 'EUR',
    'images': [],
    "depends" : ['website','spantree_logistics'],
    "data" : [
            'data/data.xml',
            'views/website_trips_booking.xml',
    ],
    'qweb': [],
    "auto_install": False,
    "installable": True,
}

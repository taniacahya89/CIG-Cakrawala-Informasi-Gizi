"""Main blueprint routes — Homepage and public pages."""

from flask import render_template
from . import main_bp


@main_bp.route('/')
def index():
    """Homepage — Beranda CIG."""
    return render_template('main/index.html')


@main_bp.route('/scan-makanan')
def scan_makanan():
    """Scan Makanan placeholder page."""
    return render_template('main/placeholder.html',
                           page_title='Scan Makanan',
                           description='Fitur Scan Makanan akan segera hadir. '
                                       'Anda akan dapat memindai makanan dan melihat '
                                       'komposisi berdasarkan panduan Isi Piringku.')

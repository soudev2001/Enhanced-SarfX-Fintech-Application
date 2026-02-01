from flask import render_template, session, redirect, url_for, request, flash, jsonify, Response
from app.routes.admin import admin_bp
from app.decorators import admin_required
from app.services.db_service import get_db, log_history
from app.services.atm_service import ATMService
from werkzeug.utils import secure_filename
from datetime import datetime
import csv
import io
import os
import json


# Configuration for photo uploads
UPLOAD_FOLDER = 'app/static/images/atms'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Moroccan cities list for forms
MOROCCAN_CITIES = [
    "Casablanca", "Rabat", "Marrakech", "Fes", "Tanger", "Agadir", "Meknes", "Oujda",
    "Kenitra", "Tetouan", "El Jadida", "Safi", "Mohammedia", "Beni Mellal", "Nador",
    "Khouribga", "Settat", "Taza", "Errachidia", "Essaouira", "Khemisset", "Larache",
    "Ksar El Kebir", "Guelmim", "Ouarzazate", "Al Hoceima", "Berkane", "Taourirt",
    "Dakhla", "Laayoune", "Tan-Tan", "Tiznit", "Taroudant", "Chefchaouen", "Ifrane", "Azrou"
]


@admin_bp.route('/atms')
@admin_required
def atms():
    """List all ATMs with filtering and pagination"""
    db = get_db()
    atm_service = ATMService(db)

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page

    # Filters
    bank_filter = request.args.get('bank', '')
    city_filter = request.args.get('city', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('q', '')

    # Build query
    query = {}
    if bank_filter:
        query['bank_code'] = bank_filter
    if city_filter:
        query['city'] = city_filter
    if status_filter:
        query['status'] = status_filter
    if search_query:
        query['$or'] = [
            {'name': {'$regex': search_query, '$options': 'i'}},
            {'address': {'$regex': search_query, '$options': 'i'}},
            {'atm_id': {'$regex': search_query, '$options': 'i'}}
        ]

    # Get ATMs
    total_atms = db.atm_locations.count_documents(query)
    atms_list = list(db.atm_locations.find(query).skip(skip).limit(per_page).sort("created_at", -1))
    total_pages = (total_atms + per_page - 1) // per_page

    # Get banks for filter
    banks = atm_service.get_all_banks()
    banks_dict = {bank['code']: bank for bank in banks}

    # Get cities for filter
    cities = atm_service.get_cities_with_atms()

    return render_template('admin/atms.html',
                         atms=atms_list,
                         banks=banks,
                         banks_dict=banks_dict,
                         cities=cities,
                         total_atms=total_atms,
                         page=page,
                         total_pages=total_pages,
                         selected_bank=bank_filter)


@admin_bp.route('/atms/dashboard')
@admin_required
def atm_dashboard():
    """ATM Analytics Dashboard"""
    db = get_db()
    atm_service = ATMService(db)

    # Basic stats
    total_atms = db.atm_locations.count_documents({})
    active_atms = db.atm_locations.count_documents({'status': 'active'})
    inactive_atms = db.atm_locations.count_documents({'status': {'$ne': 'active'}})

    # Banks data
    banks = atm_service.get_all_banks()
    banks_stats = []
    banks_chart_data = {'labels': [], 'values': [], 'colors': []}

    for bank in banks:
        count = bank.get('atm_count', 0)
        percent = round((count / total_atms * 100), 1) if total_atms > 0 else 0
        banks_stats.append({
            'name': bank['name'],
            'code': bank['code'],
            'color': bank.get('color', '#666'),
            'count': count,
            'percent': percent
        })
        banks_chart_data['labels'].append(bank['name'].split()[0])
        banks_chart_data['values'].append(count)
        banks_chart_data['colors'].append(bank.get('color', '#666'))

    # Cities data
    cities = atm_service.get_cities_with_atms()[:10]
    cities_chart_data = {
        'labels': [c['city'] for c in cities],
        'values': [c['atm_count'] for c in cities]
    }

    # Location type distribution
    location_pipeline = [
        {'$group': {'_id': '$location_type', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    location_types = list(db.atm_locations.aggregate(location_pipeline))
    location_type_data = {
        'labels': [lt['_id'] or 'Unknown' for lt in location_types],
        'values': [lt['count'] for lt in location_types]
    }

    # Services stats
    services_config = {
        'withdrawal': {'icon': 'banknote', 'color': '#22c55e'},
        'deposit': {'icon': 'wallet', 'color': '#3b82f6'},
        'balance': {'icon': 'eye', 'color': '#8b5cf6'},
        'transfer': {'icon': 'arrow-left-right', 'color': '#f59e0b'},
        'bill_payment': {'icon': 'receipt', 'color': '#ec4899'},
        'mobile_topup': {'icon': 'smartphone', 'color': '#06b6d4'}
    }

    services_stats = {}
    for svc, config in services_config.items():
        count = db.atm_locations.count_documents({'services': svc})
        percent = round((count / total_atms * 100), 1) if total_atms > 0 else 0
        services_stats[svc] = {
            'count': count,
            'percent': percent,
            'icon': config['icon'],
            'color': config['color']
        }

    # Accessibility stats
    wheelchair_count = db.atm_locations.count_documents({'has_wheelchair_access': True})
    nfc_count = db.atm_locations.count_documents({'has_nfc': True})
    deposit_count = db.atm_locations.count_documents({'has_deposit': True})
    atm_24h_count = db.atm_locations.count_documents({'available_24h': True})

    wheelchair_percent = round((wheelchair_count / total_atms * 100), 1) if total_atms > 0 else 0
    nfc_percent = round((nfc_count / total_atms * 100), 1) if total_atms > 0 else 0
    deposit_percent = round((deposit_count / total_atms * 100), 1) if total_atms > 0 else 0
    atm_24h_percent = round((atm_24h_count / total_atms * 100), 1) if total_atms > 0 else 0

    # Sources
    sources = list(db.sources.find().sort('imported_at', -1).limit(5)) if 'sources' in db.list_collection_names() else []

    return render_template('admin/atm_dashboard.html',
                         total_atms=total_atms,
                         active_atms=active_atms,
                         inactive_atms=inactive_atms,
                         banks=banks,
                         banks_stats=banks_stats,
                         banks_chart_data=json.dumps(banks_chart_data),
                         cities=cities,
                         cities_chart_data=json.dumps(cities_chart_data),
                         location_type_data=json.dumps(location_type_data),
                         services_stats=services_stats,
                         wheelchair_percent=wheelchair_percent,
                         nfc_percent=nfc_percent,
                         deposit_percent=deposit_percent,
                         atm_24h_percent=atm_24h_percent,
                         sources=sources)


@admin_bp.route('/atms/add', methods=['GET', 'POST'])
@admin_required
def add_atm():
    """Add new ATM"""
    db = get_db()
    atm_service = ATMService(db)

    if request.method == 'POST':
        atm_data = {
            'bank_code': request.form.get('bank_code'),
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'district': request.form.get('district', ''),
            'location': {
                'type': 'Point',
                'coordinates': [
                    float(request.form.get('longitude', 0)),
                    float(request.form.get('latitude', 0))
                ]
            },
            'location_type': request.form.get('location_type', 'branch'),
            'services': request.form.getlist('services'),
            'available_24h': 'available_24h' in request.form,
            'hours': request.form.get('hours') if 'available_24h' not in request.form else None,
            'has_wheelchair_access': 'has_wheelchair_access' in request.form,
            'has_nfc': 'has_nfc' in request.form,
            'has_deposit': 'has_deposit' in request.form,
            'has_audio': 'has_audio' in request.form,
            'status': 'active',
            'photos': []
        }

        # Handle photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo in photos[:5]:
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(f"{atm_data['bank_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}")
                    upload_path = os.path.join(UPLOAD_FOLDER, atm_data['bank_code'])
                    os.makedirs(upload_path, exist_ok=True)
                    filepath = os.path.join(upload_path, filename)
                    photo.save(filepath)
                    atm_data['photos'].append(f"/static/images/atms/{atm_data['bank_code']}/{filename}")

        result = atm_service.add_atm(atm_data)

        if result:
            log_history("ATM_CREATE", f"ATM {result.get('atm_id')} cree a {atm_data['city']}", user=session.get('email'))
            flash(f"ATM cree avec succes: {result.get('atm_id')}", "success")
            return redirect(url_for('admin.atms'))
        else:
            flash("Erreur lors de la creation de l'ATM", "error")

    banks = atm_service.get_all_banks()
    return render_template('admin/atm_form.html', atm=None, banks=banks, cities=MOROCCAN_CITIES)


@admin_bp.route('/atms/<atm_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_atm(atm_id):
    """Edit existing ATM"""
    db = get_db()
    atm_service = ATMService(db)

    atm = atm_service.get_atm_by_id(atm_id)
    if not atm:
        flash("ATM non trouve", "error")
        return redirect(url_for('admin.atms'))

    if request.method == 'POST':
        update_data = {
            'bank_code': request.form.get('bank_code'),
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'district': request.form.get('district', ''),
            'location': {
                'type': 'Point',
                'coordinates': [
                    float(request.form.get('longitude', 0)),
                    float(request.form.get('latitude', 0))
                ]
            },
            'location_type': request.form.get('location_type', 'branch'),
            'services': request.form.getlist('services'),
            'available_24h': 'available_24h' in request.form,
            'hours': request.form.get('hours') if 'available_24h' not in request.form else None,
            'has_wheelchair_access': 'has_wheelchair_access' in request.form,
            'has_nfc': 'has_nfc' in request.form,
            'has_deposit': 'has_deposit' in request.form,
            'has_audio': 'has_audio' in request.form,
            'status': request.form.get('status', 'active')
        }

        # Handle removed photos
        remove_photos = request.form.getlist('remove_photos')
        current_photos = atm.get('photos', [])
        update_data['photos'] = [p for p in current_photos if p not in remove_photos]

        # Handle new photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and photo.filename and allowed_file(photo.filename):
                    filename = secure_filename(f"{update_data['bank_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{photo.filename}")
                    upload_path = os.path.join(UPLOAD_FOLDER, update_data['bank_code'])
                    os.makedirs(upload_path, exist_ok=True)
                    filepath = os.path.join(upload_path, filename)
                    photo.save(filepath)
                    update_data['photos'].append(f"/static/images/atms/{update_data['bank_code']}/{filename}")

        if atm_service.update_atm(atm_id, update_data):
            log_history("ATM_UPDATE", f"ATM {atm_id} modifie", user=session.get('email'))
            flash("ATM mis a jour avec succes", "success")
            return redirect(url_for('admin.atms'))
        else:
            flash("Erreur lors de la mise a jour", "error")

    banks = atm_service.get_all_banks()
    return render_template('admin/atm_form.html', atm=atm, banks=banks, cities=MOROCCAN_CITIES)


@admin_bp.route('/atms/<atm_id>/view')
@admin_required
def view_atm(atm_id):
    """View ATM details"""
    db = get_db()
    atm_service = ATMService(db)

    atm = atm_service.get_atm_by_id(atm_id)
    if not atm:
        flash("ATM non trouve", "error")
        return redirect(url_for('admin.atms'))

    bank = atm_service.get_bank_by_code(atm.get('bank_code'))

    return render_template('admin/atm_view.html', atm=atm, bank=bank)


@admin_bp.route('/atms/<atm_id>/toggle', methods=['POST'])
@admin_required
def toggle_atm(atm_id):
    """Toggle ATM status"""
    db = get_db()

    atm = db.atm_locations.find_one({'atm_id': atm_id})
    if atm:
        new_status = 'inactive' if atm.get('status') == 'active' else 'active'
        db.atm_locations.update_one(
            {'atm_id': atm_id},
            {'$set': {'status': new_status, 'updated_at': datetime.now()}}
        )
        log_history("ATM_TOGGLE", f"ATM {atm_id} -> {new_status}", user=session.get('email'))
        return jsonify({'success': True, 'new_status': new_status})

    return jsonify({'success': False, 'error': 'ATM non trouve'}), 404


@admin_bp.route('/atms/<atm_id>/delete', methods=['POST'])
@admin_required
def delete_atm(atm_id):
    """Delete ATM (soft delete)"""
    db = get_db()
    atm_service = ATMService(db)

    if atm_service.delete_atm(atm_id):
        log_history("ATM_DELETE", f"ATM {atm_id} supprime", user=session.get('email'))
        flash("ATM supprime", "success")
    else:
        flash("Erreur lors de la suppression", "error")

    return redirect(url_for('admin.atms'))


@admin_bp.route('/atms/bulk', methods=['POST'])
@admin_required
def bulk_atm_action():
    """Bulk actions on ATMs"""
    db = get_db()

    data = request.get_json()
    action = data.get('action')
    atm_ids = data.get('atm_ids', [])

    if not atm_ids:
        return jsonify({'success': False, 'error': 'No ATMs selected'}), 400

    if action == 'activate':
        db.atm_locations.update_many(
            {'atm_id': {'$in': atm_ids}},
            {'$set': {'status': 'active', 'updated_at': datetime.now()}}
        )
        log_history("ATM_BULK_ACTIVATE", f"{len(atm_ids)} ATMs actives", user=session.get('email'))

    elif action == 'deactivate':
        db.atm_locations.update_many(
            {'atm_id': {'$in': atm_ids}},
            {'$set': {'status': 'inactive', 'updated_at': datetime.now()}}
        )
        log_history("ATM_BULK_DEACTIVATE", f"{len(atm_ids)} ATMs desactives", user=session.get('email'))

    elif action == 'delete':
        db.atm_locations.update_many(
            {'atm_id': {'$in': atm_ids}},
            {'$set': {'status': 'deleted', 'deleted_at': datetime.now()}}
        )
        log_history("ATM_BULK_DELETE", f"{len(atm_ids)} ATMs supprimes", user=session.get('email'))

    else:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400

    return jsonify({'success': True, 'count': len(atm_ids)})


@admin_bp.route('/atms/export')
@admin_required
def export_atms():
    """Export ATMs to CSV"""
    db = get_db()

    bank_filter = request.args.get('bank', '')
    city_filter = request.args.get('city', '')

    query = {'status': {'$ne': 'deleted'}}
    if bank_filter:
        query['bank_code'] = bank_filter
    if city_filter:
        query['city'] = city_filter

    atms_list = list(db.atm_locations.find(query))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'ATM ID', 'Banque', 'Nom', 'Adresse', 'Ville', 'District',
        'Latitude', 'Longitude', 'Type', 'Services', 'Statut',
        '24h', 'Horaires', 'Acces PMR', 'NFC', 'Date creation'
    ])

    for atm in atms_list:
        coords = atm.get('location', {}).get('coordinates', [0, 0])
        writer.writerow([
            atm.get('atm_id', ''),
            atm.get('bank_code', ''),
            atm.get('name', ''),
            atm.get('address', ''),
            atm.get('city', ''),
            atm.get('district', ''),
            coords[1] if len(coords) > 1 else 0,
            coords[0] if len(coords) > 0 else 0,
            atm.get('location_type', ''),
            ','.join(atm.get('services', [])),
            atm.get('status', ''),
            'Oui' if atm.get('available_24h') else 'Non',
            atm.get('hours', ''),
            'Oui' if atm.get('has_wheelchair_access') else 'Non',
            'Oui' if atm.get('has_nfc') else 'Non',
            atm.get('created_at', '').strftime('%d/%m/%Y') if atm.get('created_at') else ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=sarfx_atms_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


@admin_bp.route('/atms/import', methods=['GET', 'POST'])
@admin_required
def import_atms():
    """Import ATMs from CSV"""
    db = get_db()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Aucun fichier selectionne", "error")
            return redirect(url_for('admin.import_atms'))

        file = request.files['file']
        if file.filename == '':
            flash("Aucun fichier selectionne", "error")
            return redirect(url_for('admin.import_atms'))

        if file and file.filename.endswith('.csv'):
            try:
                stream = io.StringIO(file.stream.read().decode('utf-8'))
                reader = csv.DictReader(stream)

                source_id = f"SRC_IMPORT_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                imported = 0
                errors = 0

                for row in reader:
                    try:
                        atm_data = {
                            'atm_id': row.get('ATM ID') or f"ATM_{row.get('Banque', 'UNK')}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{imported}",
                            'bank_code': row.get('Banque', ''),
                            'name': row.get('Nom', ''),
                            'address': row.get('Adresse', ''),
                            'city': row.get('Ville', ''),
                            'district': row.get('District', ''),
                            'location': {
                                'type': 'Point',
                                'coordinates': [
                                    float(row.get('Longitude', 0) or 0),
                                    float(row.get('Latitude', 0) or 0)
                                ]
                            },
                            'location_type': row.get('Type', 'branch'),
                            'services': row.get('Services', 'withdrawal,balance').split(','),
                            'status': row.get('Statut', 'active'),
                            'available_24h': row.get('24h', '').lower() == 'oui',
                            'hours': row.get('Horaires', ''),
                            'has_wheelchair_access': row.get('Acces PMR', '').lower() == 'oui',
                            'has_nfc': row.get('NFC', '').lower() == 'oui',
                            'source_id': source_id,
                            'created_at': datetime.now()
                        }

                        db.atm_locations.insert_one(atm_data)
                        imported += 1
                    except Exception as e:
                        errors += 1
                        print(f"Error importing row: {e}")

                # Record source
                db.sources.insert_one({
                    'source_id': source_id,
                    'type': 'csv_import',
                    'name': f"Import CSV - {file.filename}",
                    'total_atms': imported,
                    'errors': errors,
                    'imported_at': datetime.now(),
                    'imported_by': session.get('email'),
                    'status': 'completed'
                })

                log_history("ATM_IMPORT", f"{imported} ATMs importes depuis {file.filename}", user=session.get('email'))
                flash(f"{imported} ATMs importes avec succes ({errors} erreurs)", "success")
                return redirect(url_for('admin.atms'))

            except Exception as e:
                flash(f"Erreur lors de l'import: {str(e)}", "error")
        else:
            flash("Format de fichier invalide (CSV requis)", "error")

    return render_template('admin/atm_import.html')

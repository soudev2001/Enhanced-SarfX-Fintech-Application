from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.decorators import login_required
from app.services.db_service import get_db, log_history
from bson.objectid import ObjectId

supplier_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@supplier_bp.route('/')
@login_required
def list_suppliers():
    db = get_db()
    suppliers = list(db.suppliers.find())
    return render_template('suppliers.html', suppliers=suppliers)

@supplier_bp.route('/add', methods=['POST'])
@login_required
def add_supplier():
    name = request.form.get('name')
    api_url = request.form.get('api_url')
    
    db = get_db()
    db.suppliers.insert_one({"name": name, "api_url": api_url, "status": "active"})
    
    log_history("ADD_SUPPLIER", f"Added supplier {name}")
    flash("Supplier added", "success")
    return redirect(url_for('suppliers.list_suppliers'))

@supplier_bp.route('/delete/<id>')
@login_required
def delete_supplier(id):
    db = get_db()
    db.suppliers.delete_one({"_id": ObjectId(id)})
    log_history("DELETE_SUPPLIER", f"Deleted supplier {id}")
    return redirect(url_for('suppliers.list_suppliers'))
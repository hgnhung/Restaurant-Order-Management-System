from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from controllers.admin_controller import AdminController
from models.menu_model import Dish
from database import get_connection

admin_bp = Blueprint("admin", __name__)
controller = AdminController()

def get_current_admin():
    return session.get("userID", "E01")

@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    if "userID" not in session:
        session["userID"] = "E01"
    return render_template("admin/dashboard.html")

@admin_bp.route('/admin/menu', methods=['GET', 'POST'])
def manage_menu():
    admin_id = get_current_admin()
    if request.method == 'POST':
        action = request.form.get('action')
        category_id = request.form.get('categoryID', 'CATE01')
        
        if action in ['add', 'update'] and category_id:
            try:
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM Category WHERE categoryID = ?", (category_id,))
                    exists = cursor.fetchone()[0]
                    
                    if exists == 0:
                        auto_name = f"Group {category_id}"
                        cursor.execute(
                            "INSERT INTO Category (categoryID, categoryName, description, status) VALUES (?, ?, ?, 'Active')",
                            (category_id, auto_name, "Auto-created by system")
                        )
                        conn.commit()
                    conn.close()
            except Exception as e:
                print(f"Auto-create category log: {e}")

        dish = Dish(
            dish_id=request.form.get('dishID'),
            name=request.form.get('name'),
            image=request.form.get('image'),
            description=request.form.get('description'),
            ingredients=request.form.get('ingredients'),
            price=float(request.form.get('price', 0)),
            is_available='isAvailable' in request.form,
            category_id=category_id
        )
        
        if action == 'add':
            if controller.addDish(dish, admin_id):
                flash("New dish added to the menu successfully!", "success")
            else:
                flash("Failed to add new dish. Please check if Dish ID already exists.", "danger")
        elif action == 'update':
            if controller.updateDish(dish, admin_id):
                flash("Dish information updated successfully!", "success")
            else:
                flash("Failed to update dish information. Please try again.", "danger")
                
        return redirect(url_for('admin.manage_menu'))
        
    dishes = controller.get_all_dishes()
    categories = controller.get_all_categories()
    return render_template('admin/menu.html', dishes=dishes, categories=categories)

@admin_bp.route('/admin/menu/delete/<string:dish_id>')
def delete_dish(dish_id):
    admin_id = get_current_admin()
    if controller.deleteDish(dish_id, admin_id):
        flash(f"Dish '{dish_id}' has been deleted successfully from the system.", "success")
    else:
        flash("Failed to delete the dish. It might be referenced in existing orders.", "danger")
    return redirect(url_for('admin.manage_menu'))

@admin_bp.route('/admin/staff', methods=['GET', 'POST'])
def manage_staff():
    admin_id = get_current_admin()
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('userID')
        
        staff_data = {
            'userID': user_id,
            'fullName': request.form.get('fullName'),
            'phone': request.form.get('phone'),
            'position': request.form.get('position'),
            'pin': request.form.get('pin'),
            'isActive': 1 if request.form.get('isActive') == '1' or 'isActive' in request.form else 0
        }
        
        if action == 'add':
            if controller.addStaff(staff_data, admin_id):
                flash(f"Employee account for {staff_data['fullName']} created successfully!", "success")
            else:
                flash("Failed to create employee account. ID might be duplicated.", "danger")
        elif action == 'update':
            if controller.updateStaff(user_id, staff_data, admin_id):
                flash(f"Employee profile for ID {user_id} updated successfully!", "success")
            else:
                flash("Failed to update employee information. Please verify data.", "danger")
            
        return redirect(url_for('admin.manage_staff'))
        
    staff_list = controller.get_all_staff_admin()
    return render_template('admin/staff.html', staff_list=staff_list)

@admin_bp.route('/admin/staff/deactivate/<string:user_id>')
def deactivate_staff(user_id):
    admin_id = get_current_admin()
    if controller.deactivateStaff(user_id, admin_id):
        flash(f"Employee account {user_id} has been deactivated successfully.", "success")
    else:
        flash("Failed to deactivate employee account.", "danger")
    return redirect(url_for('admin.manage_staff'))

@admin_bp.route('/admin/report', methods=['GET', 'POST'])
def view_report():
    report_data = None
    if request.method == 'POST':
        from_date = request.form.get('fromDate')
        to_date = request.form.get('toDate')
        report_type = request.form.get('reportType', 'Sales Report')
        
        if from_date and to_date:
            report_data = controller.generateRevenueReport(from_date, to_date, report_type)
            if report_data and report_data.reportID != "ERR01":
                flash(f"{report_type} statistics calculated successfully from database!", "success")
            else:
                flash("No invoice data found or an error occurred during calculation for the selected dates.", "danger")
            
    return render_template('admin/report.html', report=report_data)

@admin_bp.route('/admin/report/export', methods=['POST'])
def export_report():
    from_date = request.form.get('fromDate')
    to_date = request.form.get('toDate')
    report_type = request.form.get('reportType', 'Sales Report')
    file_format = request.form.get('format')
    
    if from_date and to_date and file_format:
        filename = controller.exportReportFile(from_date, to_date, report_type, file_format)
        flash(f"Report file {filename} exported successfully to device!", "success")
        
    return redirect(url_for('admin.view_report'))
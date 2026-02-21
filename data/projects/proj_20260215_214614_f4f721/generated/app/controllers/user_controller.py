from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import db
from app.models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def list_users():
    """Handles GET requests to list all users."""
    try:
        users = User.query.all()
        return render_template('users/list.html', users=users)
    except Exception as e:
        flash(f"Error fetching users: {str(e)}", "danger")
        return render_template('problem.html')

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Handles GET requests to retrieve a specific user."""
    try:
        user = User.query.get_or_404(user_id)
        return render_template('users/detail.html', user=user)
    except Exception as e:
        flash(f"Error fetching user: {str(e)}", "danger")
        return render_template('problem.html')

@user_bp.route('/users/new', methods=['GET', 'POST'])
def create_user():
    """Handles GET and POST requests to create a new user."""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            new_user = User(username=username, email=email)
            db.session.add(new_user)
            db.session.commit()
            flash("User created successfully!", "success")
            return redirect(url_for('user.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating user: {str(e)}", "danger")
    return render_template('users/new.html')

@user_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Handles GET and POST requests to edit a user."""
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.email = request.form['email']
            db.session.commit()
            flash("User updated successfully!", "success")
            return redirect(url_for('user.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating user: {str(e)}", "danger")
    return render_template('users/edit.html', user=user)

@user_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Handles POST requests to delete a user."""
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
        return redirect(url_for('user.list_users'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "danger")
        return redirect(url_for('user.list_users'))
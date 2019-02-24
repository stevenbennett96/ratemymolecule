from rmm import app
from flask import render_template, jsonify, request, redirect, url_for, flash
from rmm import auth
import numpy as np
from sqlalchemy import func
from flask_login import login_required, current_user
from rmm import db
from rmm.forms import ResetPasswordRequestForm, ResetPasswordForm
from rmm.models import User, Score, Molecule
from rmm.email import send_password_reset_email


# Default index route to load the home page
@app.route('/')
@app.route('/index')
def index():
    return render_template('main/index.html', title='Home Page')

@login_required
@app.route('/score', methods=['POST'])
def score():
    # Just get a random molecule for the time being
    # Gets the current user
    user = db.session.query(User).get(current_user.id)
    # Check unsure was not clicked
    if int(request.form['score']) != 2:
        user.score_mol(score=request.form['score'], molecule_id=request.form['id'])
        db.session.commit()

    return get_mol_not_scored()

# Code to remove the molecule
@login_required
@app.route('/remove', methods=['POST'])
def remove():
    user = db.session.query(User).get(current_user.id)
    # Find the score that needs to be removed from the button.
    score_id = int(request.form['score_id'])
    # Gets the score.
    score = db.session.query(Score).get(score_id)
    # Function that checks that the current logged in user has actually scored this molecule
    def check_score():
        for score in user.scores:
            if score_id == score.id:
                return True
            else:
                continue
    if check_score():
        db.session.delete(score)
        db.session.commit()
    return jsonify({'score_id': score_id})

@login_required
@app.route('/change_score', methods=['POST'])
def change_score():
    user = db.session.query(User).get(current_user.id)
    # Find the score that needs to be removed from the button.
    score_id = int(request.form['score_id'])
    # Gets the score.
    score = db.session.query(Score).get(score_id)
    sco = int(score.sco)

    # Function that checks that the current logged in user has actually scored this molecule
    def check_score():
        for score in user.scores:
            if score_id == score.id:
                return True
            else:
                continue
    if check_score():
        if sco == 1:
            score.sco = 0
        else:
            score.sco = 1
        db.session.commit()
    return jsonify({'score_id': score_id})

# Get a random molecule function
def get_rand_mol():
    # Function gets a random molecule from the database to display on the website
    idx = np.random.randint(1, db.session.query(Molecule).count())
    molecule = db.session.query(Molecule).get(idx)

    return molecule

# This function returns a molecule that has not been scored yet to the user
@app.route('/get_mol_not_scored', methods=['GET'])
def get_mol_not_scored():
    # Get a molecule that has not been scored by the user
    while True:
        molecule = get_rand_mol()
        for score in molecule.scores:
            if int(score.id) == current_user.id:
                continue
        break
    return jsonify({'id':molecule.id,
                   'smiles':molecule.mol})

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    # Sanity check to see if the user is actually logged in.
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password.')
        return redirect(url_for('auth.login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

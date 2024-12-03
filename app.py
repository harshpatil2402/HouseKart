#importing necessary libraries
##############################


from flask import Flask, render_template, url_for, flash, redirect, request, session, Response, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from sqlalchemy import and_
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField,SelectField,SubmitField, EmailField, TextAreaField, IntegerField
from wtforms.validators import NumberRange, DataRequired, Email, EqualTo, Length, Optional
from flask_login import login_user,logout_user,login_required,current_user, LoginManager, UserMixin
import os




##############################

#Instatiating a Flask class object and Sqlalchemy object

app = Flask(__name__)
#db = SQLAlchemy(app)


# Configuring Necessary Settings
##############################

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['SECRET_KEY'] = 'secretkeysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'home'
login_manager.login_message_category = 'warning' 

##############################


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

import os
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])  # Create the folder if it doesn't exist




 
# Defining database tables
##############################

#1.Customer
class Customer(db.Model):  
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)  
    email = db.Column(db.String(255), unique=True, nullable=False)  
    full_name = db.Column(db.String(255), nullable=False)  
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(15), nullable=False)  
    address = db.Column(db.String(255), nullable=False)  
    pincode = db.Column(db.String(6), nullable=False)  
    date_created = db.Column(db.Date, nullable=False, default=datetime.now().date)  
    is_blocked = db.Column(db.Boolean, default=False)
    services = db.relationship('ServiceRequest', backref='servicecustomer', lazy=True)
    user = db.relationship('User', backref='customer', uselist=False)

    def __repr__(self):  
        return f"({self.email}, {self.full_name}, {self.address}, {self.pincode})"  

#2.Professional
class Professional(db.Model):  
    __tablename__ = 'professional'
    id = db.Column(db.Integer, primary_key=True)  
    email = db.Column(db.String(255), unique=True, nullable=False)  
    full_name = db.Column(db.String(255), nullable=False)  
    password = db.Column(db.String(255), nullable=False) 
    contact = db.Column(db.String(15), nullable=False)
    service_type = db.Column(db.String(255), nullable=False)  
    service_description = db.Column(db.Text, nullable=False)  
    experience = db.Column(db.String(255), nullable=False)  
    document = db.Column(db.String(255), nullable=False)  
    address = db.Column(db.String(255), nullable=False)  
    pincode = db.Column(db.String(6), nullable=False)  
    date_created = db.Column(db.Date, nullable=False, default=datetime.now().date)  
    is_blocked = db.Column(db.Boolean, default=False)  
    is_approved = db.Column(db.Boolean, default=False) 
    services = db.relationship('ServiceRequest', backref='serviceprofessional', lazy=True)
    user = db.relationship('User', backref='professional', uselist=False)

    def __repr__(self):  
        return f"({self.email}, {self.full_name}, {self.service_type}, {self.service_description}, {self.experience}, {self.address}, {self.pincode})"


#3. User model (Common table for Customers and Professionals)
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)  
    email = db.Column(db.String(255), unique=True, nullable=False)  
    full_name = db.Column(db.String(255), nullable=False)  
    password = db.Column(db.String(255), nullable=False)  
    contact = db.Column(db.String(15), nullable=False)
    role = db.Column(db.Integer, nullable=False, default=1)  # 1 for Customer, 2 for Professional  
    is_blocked = db.Column(db.Boolean, default=False)  
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete='CASCADE')) #customer_id or professional_id can be nullable
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id', ondelete='CASCADE'))


    def __repr__(self):  
        return f"{self.id}"

    

       
#4. Allowed services by Admin
class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)  
    service_type = db.Column(db.String(255),unique=True, nullable=False)  
    service_description = db.Column(db.Text, nullable=False)  
    time_required = db.Column(db.Integer, nullable=True)  
    base_price = db.Column(db.Integer, nullable=False)
    services = db.relationship('ServiceRequest',backref='servicedetails',lazy=True)

    def __repr__(self):  
        return f"({self.service_type},{self.service_description},{self.time_required},{self.base_price})" 
   

#5. Service Request
class ServiceRequest(db.Model):   
    __tablename__ =  'servicerequest'
    id = db.Column(db.Integer, primary_key=True)  
    
    # Foreign Keys  
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete='CASCADE'))  
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id', ondelete='CASCADE'))  #can be nullable
    service_id = db.Column(db.Integer, db.ForeignKey('service.id', ondelete='CASCADE'))
    request_date = db.Column(db.Date, nullable=False, default=datetime.now().date)  
    service_status = db.Column(db.String(255), nullable=False)  
    reviews = db.relationship('ServiceReview',backref='servicereq',lazy=True,uselist=False)
    
    def __repr__(self):  
        return f"({self.customer_id},{self.professional_id},{self.service_id},{self.request_date},{self.service_status})" 
    

#6.Rejected Services by Professionals
class RejectedServiceRequest(db.Model):
    __tablename__ = 'rejected_service_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id', ondelete='CASCADE'))
    service_request_id = db.Column(db.Integer, db.ForeignKey('servicerequest.id', ondelete='CASCADE'))
    rejection_date = db.Column(db.DateTime, default=datetime.now().date, nullable=False)
    professional = db.relationship('Professional', backref='rejected_requests', lazy=True)
    service_request = db.relationship('ServiceRequest', backref='rejections', lazy=True)

#7. Service Review by Customers
class ServiceReview(db.Model):   
    __tablename__ = 'servicereview'
    id = db.Column(db.Integer, primary_key=True)
    completion_date = db.Column(db.Date, nullable=False, default=datetime.now().date)  
    remarks = db.Column(db.Text, nullable=False)  
    ratings = db.Column(db.Integer, nullable=False) 
    service_request_id = db.Column(db.Integer, db.ForeignKey('servicerequest.id', ondelete='CASCADE'))
  
    def __repr__(self):  
        return f"({self.completion_date}, {self.remarks}, {self.ratings})" 


##############################



#Defining various required forms
##############################

#1.Login Form for customer,professionals,admin
class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired()])

    password = PasswordField('Password',validators=[DataRequired()])

    submit = SubmitField('Login')


#2.Customer Signup Form
class CustomerSignupForm(FlaskForm):
    email = StringField('Register Email Id',validators=[DataRequired()])

    password = PasswordField('Password',validators=[DataRequired(),])

    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password',message="Passwords must match.")],)
    
    full_name = StringField('Full Name',validators=[DataRequired()],)

    contact = StringField('Contact Number',validators=[DataRequired()])

    address = StringField('Address',validators=[DataRequired()])

    pincode = StringField('Pincode',validators=[DataRequired(),Length(6, 6, message="Pincode must be 6 digits.")])

    submit = SubmitField('Submit')

#2.Customer Signup Form
class CustomerUpdateForm(FlaskForm):
    email = StringField('Registered Email Id',validators=[DataRequired()])

    full_name = StringField('Full Name',validators=[DataRequired()],)

    contact = StringField('Contact Number',validators=[DataRequired()])

    address = StringField('Address',validators=[DataRequired()])

    pincode = StringField('Pincode',validators=[DataRequired(),Length(6, 6, message="Pincode must be 6 digits.")])

    submit = SubmitField('Submit')



#3. Professional Signup Form
class ProfessionalSignupForm(FlaskForm):
    email = StringField('Register Email Id',validators=[DataRequired()])

    password = PasswordField('Password',validators=[DataRequired(),Length(min=6, message="Password must be at least 6 characters long.")],)

    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password', message="Passwords must match.")],)
    
    full_name = StringField('Full Name',validators=[DataRequired()],)

    contact = StringField('Contact Number',validators=[DataRequired()])
    
    service_type = SelectField('Service Type',validators=[DataRequired()],)
    
    service_description = TextAreaField('Service Description',validators=[DataRequired()])
    
    experience = StringField('Experience',validators=[DataRequired()])
    
    document = FileField('Document for Verification',validators=[DataRequired(),FileAllowed(['jpg', 'png', 'pdf', 'jpeg'])])
    
    address = StringField('Address',validators=[DataRequired()])
    
    pincode = StringField('Pincode',validators=[DataRequired(),Length(6, 6, message="Pincode must be 6 digits.")],)
    
    submit = SubmitField('Submit')

#3. Professional Signup Form
class ProfessionalUpdateForm(FlaskForm):
    email = StringField('Registered Email Id',validators=[DataRequired()])

    full_name = StringField('Full Name',validators=[DataRequired()],)

    contact = StringField('Contact Number',validators=[DataRequired()])
    
    service_description = TextAreaField('Service Description',validators=[DataRequired()])
    
    address = StringField('Address',validators=[DataRequired()])
    
    pincode = StringField('Pincode',validators=[DataRequired(),Length(6, 6, message="Pincode must be 6 digits.")],)
    
    submit = SubmitField('Submit')



#4. Form for Adding/Editing New service by admin
class AddNewService(FlaskForm):
    service_type = StringField('Service Name',validators=[DataRequired()])

    service_description = TextAreaField('Service Description',validators=[DataRequired()])

    base_price = IntegerField('Base Price',validators=[DataRequired()])

    time_required = IntegerField('Time Required(in hrs)',validators=[Optional()])

    submit = SubmitField('Submit')


#5. Ratings Form by customer
class Ratings(FlaskForm):
    service_ratings = IntegerField('Ratings (out of 5)',validators=[ DataRequired(message="Please provide a rating."),NumberRange(min=1, max=5, message="Ratings must be between 1 and 5.")])
    
    service_remarks = TextAreaField('Service Remarks/Complaints (if any)',validators=[DataRequired(message="Please provide remarks or leave a note."),Length(max=500, message="Remarks should not exceed 500 characters.")])
    
    submit = SubmitField('Submit')


##############################



# Creating Database
##############################
with app.app_context():
    db.drop_all() #for development purpose
    db.create_all()
##############################





#Defining App routes
##############################

#1. Login route common for all
@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@housekart.in' and form.password.data == 'housekart':
            #flash('Welcome Admin', 'success')
            return redirect(url_for('adminhome'))

        # Retrieve the user
        user = User.query.filter_by(email=form.email.data).first()
        email1 = form.email.data
        
        # Initialize variables
        custblocked = None
        profblocked = None

        # Check if the customer is blocked
        try:
            customer = Customer.query.filter_by(email=email1).first()
            if customer:
                custblocked = customer.is_blocked
        except Exception as e:
            pass
        
        # Check if the professional is blocked
        try:
            professional = Professional.query.filter_by(email=email1).first()
            if professional:
                profblocked = professional.is_blocked
        except Exception as e:
            pass

        if user and user.password == form.password.data:
            # Redirect based on role and check if user is blocked
            if user.role == 1 and not custblocked:
                login_user(user)  
                flash(f'Logged in as {user.email}!', 'success')
                return redirect(url_for('customerhome'))
            
            elif user.role == 1 and custblocked:
                return render_template('blocked.html')
            
            elif user.role == 2 and not profblocked:
                # if professional not blocked Check professional approval status
                approval = professional.is_approved if professional else False
                if approval:
                    login_user(user)  
                    flash(f'Logged in as {user.email}!', 'success')
                    return redirect(url_for('professionalhome', professional_id=professional.id))
                else:
                    return render_template('approvalawaited2.html', title='Approval awaited')

            else: #blocked professional
                return render_template('blocked.html')

        flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('home.html', title='Home', form=form)


#2. Empty route
@app.route('/#')
def _():
    pass

#3. Professional Signup
@app.route('/profsignup',methods=['GET','POST'])
def profsignup():
    form=ProfessionalSignupForm()
    services = Service.query.all()  # services dropdown
    form.service_type.choices = [(service.service_type, f"{service.service_type} - {service.service_description}") for service in services] #cant be defined before hence adding at current moment

    if form.validate_on_submit():
        try :
            document = form.document.data

            if document and document.filename != '':
                # Extract file extension and create a filename directly using the email
                file_extension = document.filename.rsplit('.', 1)[1].lower()  # Get file extension
                if file_extension not in ['pdf', 'png', 'jpg', 'jpeg']:
                    flash('Invalid file type. Please upload a PDF, PNG, JPG, or JPEG file.', 'danger')
                    return redirect(request.url)

                filename = f"{form.email.data}.{file_extension}"
                upload_folder = app.config['UPLOAD_FOLDER']
                
            #Getting form data and adding in Professional Table
            professional = Professional(
                email=form.email.data,
                full_name=form.full_name.data,
                password=form.password.data,
                contact=form.contact.data,
                service_type=form.service_type.data,
                service_description=form.service_description.data,
                experience=form.experience.data,
                document=filename,
                address=form.address.data,
                pincode=form.pincode.data
            )
            db.session.add(professional)
            db.session.commit()
            

            

            # add as user
            user = User(
                email=professional.email,
                full_name=professional.full_name,
                password=professional.password,
                contact=professional.contact,
                role=2,#2 for prof
                professional_id=professional.id
            )
            db.session.add(user)
            db.session.commit()
            file_path = os.path.join(upload_folder, filename)
            document.save(file_path) 
            
            # if registered successfully, informing Professional
            flash(f'Account created for {form.full_name.data}!', 'success')
            approval = Professional.query.filter_by(email = professional.email).first().is_approved
            if approval:
                return redirect(url_for('home'))
            else:
                return render_template('approvalawaited.html',title='Approval awaited')

# if professional already exist
        except Exception as e:
            flash(f'This user already exist, Please login as {form.email.data}' ,'danger')
            return redirect(url_for('home'))
    return render_template('professional_signup.html',title='SignUp as a professional',form=form,show_navbar=False)


#Customer Signup
@app.route('/signup',methods=['GET','POST'])
def signup():
    form=CustomerSignupForm()
    if form.validate_on_submit():
        try:
            #Getting form data and adding in Customer Table
            customer=Customer(email=form.email.data,
                              full_name=form.full_name.data,
                              password=form.password.data,
                              contact=form.contact.data,
                              address=form.address.data,
                              pincode=form.pincode.data)
            
            db.session.add(customer)
            db.session.commit()
            #adding same details in user but different role
            user = User(email=form.email.data,
                        full_name=form.full_name.data,
                        password=form.password.data,
                        contact=form.contact.data,
                        role=1,customer_id=customer.id)
            db.session.add(user)
            db.session.commit()

           
            flash(f'Account created for {form.full_name.data}!','success')
            return redirect(url_for('home'))
        # if customer already exist
        except Exception as e:
            flash(f'This user already exist, Please login as {form.email.data}' ,'danger')
            return redirect(url_for('home'))
    return render_template('signup_as_customer.html',title='Signup',form=form,show_navbar=False)

@app.route('/adminhome', methods=['GET', 'POST'])  
def adminhome():  
    #Querying required tables and filtering according to need 
    services = Service.query.all()
    professionals = Professional.query.all()
    approved_professional = Professional.query.filter_by(is_approved=True).with_entities(Professional.id).all()
    blocked_professional = Professional.query.filter_by(is_blocked=True).with_entities(Professional.id).all()
    customers = Customer.query.all()
    blocked_customer = Customer.query.filter_by(is_blocked=True).with_entities(Customer.id).all()
    service_requests = ServiceRequest.query.order_by(ServiceRequest.service_status.desc()).all()


#gwtting all actions clicked by admin
    action = request.form.get('action')
    action2 = request.form.get('action2')
    action3 = request.form.get('blockprof')
    service_id = request.form.get('service_id')
    professional_approval = request.form.get("profapproval")
    block_prof_id = request.form.get('professional_id')
    approve_prof_id = request.form.get('approve_professional_id')
    block_customer_id = request.form.get("customer_id")
    block_customer = request.form.get('blockcustomer')
    unblock_customer_id = request.form.get('unblock_customer_id')
    unblock_customer = request.form.get('unblockcustomer')
    unblock_professional = request.form.get('unblockprof')
    unblock_professional_id = request.form.get('unblockprofessional_id')

    #Block Customer
    if block_customer == 'blockcustomer':
        block_cust = Customer.query.filter_by(id = block_customer_id).first()
        block_cust.is_blocked = True
        db.session.commit()
        flash(f'Customer {block_cust.full_name} was blocked','danger')
        return redirect(url_for('adminhome'))
    
    #Unblock Customer 
    if unblock_customer == 'unblockcustomer':
        unblock_cust = Customer.query.filter_by(id = unblock_customer_id).first()
        unblock_cust.is_blocked = False
        db.session.commit()
        flash(f'Customer {unblock_cust.full_name} was unblocked','success')
        return redirect(url_for('adminhome'))

    # Block Professional
    if action3 == 'blockprof':
        block_prof = Professional.query.filter_by(id=block_prof_id).first()
        if not block_prof.is_blocked:
            block_prof.is_blocked = True
            db.session.commit()
            flash(f'Professional {block_prof.full_name} was blocked successfully', 'warning')
        else:
            flash('This Professional was already blocked', 'danger')
        return redirect(url_for('adminhome'))
    
    # Unblock Professional
    if unblock_professional == 'unblockprof':
        unblock_prof = Professional.query.filter_by(id=unblock_professional_id).first()
        if  unblock_prof.is_blocked:
            unblock_prof.is_blocked = False
            db.session.commit()
            flash(f'Professional {unblock_prof.full_name} was unblocked successfully', 'success')
        else:
            flash('This Professional is already unblocked', 'info')
        return redirect(url_for('adminhome'))


    # Approve/Reject Professional
    if professional_approval:
        if professional_approval == 'approve':
            approve_prof = Professional.query.filter_by(id=approve_prof_id).first()
            if approve_prof:
                approve_prof.is_approved = True
                db.session.commit()
                flash(f'Professional {approve_prof.full_name} approved successfully', 'success')
            else:
                flash("Professional not found. Cannot approve.", 'danger')
        elif professional_approval == 'reject':
            rejected_prof = Professional.query.filter_by(id=approve_prof_id).first()
            if rejected_prof:
                db.session.delete(rejected_prof)
                db.session.commit()
                flash(f"Professional {rejected_prof.full_name}'s application was rejected", 'info')
            else:
                flash("Professional not found. Cannot reject application.", 'danger')
        return redirect(url_for('adminhome'))

    # Add Service
    if action == 'addservice':
        return redirect(url_for('addservice'))

    # Edit/Delete Service
    if action2:
        if action2 == 'edit':
            return redirect(url_for('addservice', service_id=service_id))
        elif action2 == 'delete':
            delete_service = Service.query.get(service_id)
            if delete_service:
                try:
                    db.session.delete(delete_service)
                    db.session.commit()
                    flash('Service deleted successfully!', 'success')
                    return redirect(url_for('adminhome'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while deleting the service.', 'danger')
            else:
                flash('Service not found. Unable to delete.', 'danger')

    return render_template('adminhome.html',title='Admin-Home',show_navbar=True,professionals=professionals,customers=customers,services=services,service_requests=service_requests,approved_professional=approved_professional,blocked_professional=blocked_professional,blocked_customer=blocked_customer)


#4.Admin Search
@app.route('/adminsearch',methods=['GET','POST'])
def adminsearch():
#querying required table and filtering
    services = Service.query.all()
    professional= Professional.query.all()
    customer = Customer.query.all()
    service_request = ServiceRequest.query.all() 
    blocked_customer = Customer.query.filter_by(is_blocked=True).with_entities(Customer.id).all()
    approved_professional = Professional.query.filter_by(is_approved=True).with_entities(Professional.id).all()
    blocked_professional = Professional.query.filter_by(is_blocked=True).with_entities(Professional.id).all()

#getting button clicks and their value
    block_customer_id = request.form.get("customer_id")
    block_customer = request.form.get('blockcustomer')
    search_by = request.form.get('search_by')  # Dropdown value
    search_query = request.form.get('search_query')
    approve_prof_id = request.form.get('approve_professional_id')
    professional_approval = request.form.get("profapproval")
    action2 = request.form.get('action2')
    action3 = request.form.get('blockprof')
    block_prof_id = request.form.get('professional_id')
    unblock_customer_id = request.form.get('unblock_customer_id')
    unblock_customer = request.form.get('unblockcustomer')
    unblock_professional = request.form.get('unblockprof')
    unblock_professional_id = request.form.get('unblockprofessional_id')
    edit_del_service_id = request.form.get('edit_del_service_id')



    #Block Customer
    if block_customer == 'blockcustomer':
        block_cust = Customer.query.filter_by(id = block_customer_id).first()
        block_cust.is_blocked = True
        db.session.commit()
        flash(f'Customer {block_cust.full_name} was blocked','danger')
        return redirect(url_for('adminsearch'))
    
    #Unblock Customer 
    if unblock_customer == 'unblockcustomer':
        unblock_cust = Customer.query.filter_by(id = unblock_customer_id).first()
        unblock_cust.is_blocked = False
        db.session.commit()
        flash(f'Customer {unblock_cust.full_name} was unblocked','success')
        return redirect(url_for('adminhome'))
    
    # Approve/Reject Professional
    if professional_approval:
        if professional_approval == 'approve':
            approve_prof = Professional.query.filter_by(id=approve_prof_id).first()
            if approve_prof:
                approve_prof.is_approved = True
                db.session.commit()
                flash(f'Professional {approve_prof.full_name} approved successfully', 'success')
            else:
                flash("Professional not found. Cannot approve.", 'danger')
        elif professional_approval == 'reject':
            rejected_prof = Professional.query.filter_by(id=approve_prof_id).first()
            if rejected_prof:
                db.session.delete(rejected_prof)
                db.session.commit()
                flash(f"Professional {rejected_prof.full_name}'s application was rejected", 'info')
            else:
                flash("Professional not found. Cannot reject application.", 'danger')
        return redirect(url_for('adminsearch'))
    
    # Block Professional
    if action3 == 'blockprof':
        block_prof = Professional.query.filter_by(id=block_prof_id).first()
        if not block_prof.is_blocked:
            block_prof.is_blocked = True
            db.session.commit()
            flash(f'Professional {block_prof.full_name} was blocked successfully', 'warning')
        else:
            flash('This Professional was already blocked', 'danger')
        return redirect(url_for('adminsearch'))
    
     # Unblock Professional
    if unblock_professional == 'unblockprof':
        unblock_prof = Professional.query.filter_by(id=unblock_professional_id).first()
        if  unblock_prof.is_blocked:
            unblock_prof.is_blocked = False
            db.session.commit()
            flash(f'Professional {unblock_prof.full_name} was unblocked successfully', 'success')
        else:
            flash('This Professional is already unblocked', 'info')
        return redirect(url_for('adminhome'))
    
    # Edit/Delete Service
    if action2:
        if action2 == 'edit':
            return redirect(url_for('addservice', service_id=edit_del_service_id))
        elif action2 == 'delete':
            delete_service = Service.query.get(edit_del_service_id)
            if delete_service:
                try:
                    db.session.delete(delete_service)
                    db.session.commit()
                    flash('Service deleted successfully!', 'success')
                    return redirect(url_for('adminhome'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while deleting the service.', 'danger')
            else:
                flash('Service not found. Unable to delete.', 'danger')

    if search_by == 'service':
        results = Service.query.filter(Service.service_type.ilike(f"%{search_query}%")).all()
    elif search_by == 'customer':
        results = Customer.query.filter(Customer.full_name.ilike(f"%{search_query}%")).all()
    elif search_by == 'professional':
        results = Professional.query.filter(Professional.full_name.ilike(f"%{search_query}%")).all()
    else:
        results = []

     
    return render_template('adminsearch.html', title='Admin-Search', show_navbar=True,professional=professional, customer=customer,services=services,service_request=service_request,results=results,blocked_customer=blocked_customer,search_by=search_by,approved_professional=approved_professional,blocked_professional=blocked_professional)

# def coalesce(*args):
#     """
#     Returns the first non-None value from the provided arguments.
#     If all values are None, returns None.
    
#     Parameters:
#         *args: A variable number of arguments (values) to check.
        
#     Returns:
#         The first non-None value or None if all are None.
#     """
#     for arg in args:
#         if arg is not None:
#             return arg
#     return None

# def coalesce_avg_rating():
#     """
#     Returns the first non-None value between the average rating or 0.
#     """
#     avg_rating = func.avg(ServiceReview.ratings).label('average_rating')
#     return coalesce(avg_rating, 0)


#Customer Home
@app.route('/customerhome', methods=['GET','POST'])  
@login_required  
def customerhome():  
    customer = Customer.query.filter_by(email=current_user.email).first()  
    customer_id = customer.id  
    servicerequest = ServiceRequest.query.filter_by(customer_id=customer_id).order_by(ServiceRequest.service_status.desc())  
    clicked_button = request.form.get('service_asked')  
    bookservice = request.form.get('bookservice')  
    professional_book_id = request.form.get('professional_book_id')  
    service_book_type = request.form.get('service_book_type') 
    closeserviceid = request.form.get('closeserviceid')
    closeservice = request.form.get('closeservice') 
    rejectedservice = RejectedServiceRequest.query.with_entities(RejectedServiceRequest.id).all()
    

    curr_id = current_user.email  
    #cust_pincode = Customer.query.filter_by(email=curr_id).first().pincode  
    services = Service.query.order_by(Service.service_type).all()  
    
    # Book service   
    if bookservice == 'bookservice':  
        service_id_book = Service.query.filter_by(service_type=service_book_type).first().id  
        sr = ServiceRequest(customer_id=current_user.customer_id,professional_id=professional_book_id,service_id=service_id_book,service_status='Open')  
        db.session.add(sr)  
        db.session.commit()  
        flash('Service Request was booked','success')  
        return redirect(url_for('customerhome'))  

    #close service
    if closeservice == 'closeservice':
        close_serv = ServiceRequest.query.filter_by(id=closeserviceid).first()
        close_serv.service_status = 'Completed'
        db.session.commit()
        flash('Thank you for using HouseKart')      
    
    # View services to book  
    query_result = []  
    if clicked_button:  
        query_result = (
        db.session.query(
            Professional,
            Service.base_price,
            func.coalesce(func.avg(ServiceReview.ratings), 0).label('avg_rating')
        )
        .join(
            Service,
            and_(Professional.service_type == Service.service_type, Service.service_type == clicked_button)  # Filter by clicked_button
        )
        .outerjoin(ServiceRequest, and_(Professional.id == ServiceRequest.professional_id, ServiceRequest.service_status != 'rejected'))
        .outerjoin(ServiceReview, ServiceRequest.id == ServiceReview.service_request_id)
        .group_by(Professional, Service.base_price)
        .all()
    )#this query gets a list of professionals with the base price of their services and its avg rating. 
#joins the Professional table with the Service table based on service type, and optionally joins 
#ServiceRequest and ServiceReview tables to include requests (excluding rejected ones) and associated reviews.
#The average rating is calculated using `func.avg`, defaulting to 0 if no ratings exist, and results are grouped by professiona.


        # to close open services
    if closeservice == 'closeservice':
        closeservicerequest = ServiceRequest.query.filter_by(id = closeserviceid).first()
        closeserviceprof = ServiceRequest.query.filter_by(id = closeserviceid).first().professional_id
        closeservicerequest.service_status = 'Completed'
        db.session.commit()
        flash('Service was closed. Please pay our service provider partner','info') 
        return redirect(url_for('ratings',service_request_id = closeserviceid,professional_id=closeserviceprof))

        

       

    return render_template('customerhome.html',title='Customer-Home',rejectedservice=rejectedservice,show_navbar=True,services=services,servicerequest=servicerequest,clicked_button=clicked_button,query_result=query_result)  
    
    

    

#Customer Search
@app.route('/customersearch', methods=['GET', 'POST'])
@login_required
def customersearch():
    bookservice = request.form.get('bookservice')
    service_book_type = request.form.get('service_book_type')
    professional_book_id = request.form.get('professional_book_id')
    search_by = request.form.get('search_by')
    search_query = request.form.get('search_query')
    query = (db.session.query(Professional.id.label('professional_id'),Professional.full_name.label("professional_name"),Professional.address.label("address"),Professional.pincode.label("pincode"),Service.service_description.label("service_description"),Service.service_type.label("service_type"),Service.base_price.label("base_price"),func.coalesce(func.avg(ServiceReview.ratings), 0).label("average_rating")).join(ServiceRequest, ServiceRequest.professional_id == Professional.id).join(Service, Service.id == ServiceRequest.service_id).outerjoin(ServiceReview, ServiceReview.service_request_id == ServiceRequest.id).group_by(Professional.id, Service.id))

    if search_by == 'service_type':
        query = query.filter(Service.service_type.ilike(f"%{search_query}%"))
    elif search_by == 'service_description':
        query = query.filter(Service.service_description.ilike(f"%{search_query}%"))
    elif search_by == 'address':
        query = query.filter(Professional.address.ilike(f"%{search_query}%"))
    elif search_by == 'pincode':
        query = query.filter(Professional.pincode.ilike(f"%{search_query}%"))
    results = query.all()

    #book service 
    if bookservice == 'bookservice':
        service_id_book = Service.query.filter_by(service_type=service_book_type).first().id
        sr = ServiceRequest(customer_id=current_user.customer_id,professional_id=professional_book_id,service_id=service_id_book,service_status='Open')
        db.session.add(sr)
        db.session.commit()
        flash('Service Request was booked','success')
        return redirect(url_for('customerhome'))  
    

    return render_template('customersearch.html', title='Customer-Search', show_navbar=True,results=results)



#External function that i will use for rejecting customer requesting
def reject_service(professional_id, service_request_id):
    rejection = RejectedServiceRequest(professional_id=professional_id,service_request_id=service_request_id)
    db.session.add(rejection)
    db.session.commit()



#Professional Home
@app.route('/professionalhome', methods=['GET', 'POST'])
@login_required
def professionalhome():
    professional = Professional.query.filter_by(email=current_user.email).first()
    servicerequest = ServiceRequest.query.filter_by(service_status='Open').all()
    id = professional.id
    currentservicerequest = ServiceRequest.query.filter_by(professional_id=id, service_status='Pending').all()
    servicerequestclose = ServiceRequest.query.filter_by(professional_id=id, service_status='Completed').all()
    rejected_services = RejectedServiceRequest.query.filter_by(professional_id=id).with_entities(RejectedServiceRequest.service_request_id).all()
    

    if request.method == 'POST':
        requestaction = request.form.get('clickedbutton')
        service_request_id = request.form.get('service_request_id')

        #accepting a request by customer
        if requestaction == 'accept' and service_request_id:
            servicerequest_to_accept = ServiceRequest.query.get(service_request_id)
            
            #Accepting request that has service request open
            if servicerequest_to_accept and servicerequest_to_accept.service_status == 'Open' and (ServiceRequest.query.filter_by(service_status='Pending',professional_id = id).count() == 0):
                servicerequest_to_accept.service_status = 'Pending'
                servicerequest_to_accept.professional_id = id  
                db.session.commit()
                flash(f'Service Request for {servicerequest_to_accept.servicecustomer.full_name} has been accepted','success')
                
            #Accepting only one request at a time
            else:
                flash('You have one service open currently. Kindly ask customer of that service to close it, if already done','warning')
            return redirect(url_for('professionalhome'))    
        #Rejecting a service of customer
        elif requestaction == 'reject' and service_request_id:
            reject_service(id,service_request_id)
            flash('Rejected','danger')
            return redirect(url_for('professionalhome'))
    return render_template('professionalhome.html',title='Professional-Home',show_navbar=True,servicerequest=servicerequest,servicerequestclose=servicerequestclose,currentservicerequest=currentservicerequest,rejected_services=rejected_services)


#Professional Search
@app.route('/professionalsearch', methods=['GET', 'POST'])
@login_required
def professionalsearch():
    professional = Professional.query.filter_by(email=current_user.email).first()
    professional_id = professional.id
    search_by = request.form.get('search_by')  
    search_query = request.form.get('search_query')  

    
    if not search_by or not search_query:
        results = []  
    else: #filtering db by search query in relevant tables
        if search_by == 'location':
            results = ServiceRequest.query.filter_by(professional_id=professional_id).filter(Customer.address.ilike(f"%{search_query}%")).all()
        elif search_by == 'name':
            results = ServiceRequest.query.filter_by(professional_id=professional_id).filter(Customer.full_name.ilike(f"%{search_query}%")).all()
        elif search_by == 'pincode':
            results = ServiceRequest.query.filter_by(professional_id=professional_id).filter(Customer.pincode.ilike(f"%{search_query}%")).all()
        else:
            results = []
    return render_template('professionalsearch.html',title='Professional-Search',show_navbar=True,results=results, search_by=search_by)


#logging out current use
@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out','warning')
    return redirect(url_for('home'))


#Showing account details to current user
@app.route('/account')
@login_required
def account():
    return render_template('account.html',title='Account',show_navbar=True)


#adding and editing services by admin
@app.route('/addservice', methods=['GET', 'POST'])
@app.route('/addservice/<int:service_id>', methods=['GET', 'POST'])
def addservice(service_id=None):
    form = AddNewService()
    service = Service.query.get(service_id)
    if form.validate_on_submit():
        try:
            if service:
                # Update the existing service
                service.service_type = form.service_type.data
                service.service_description = form.service_description.data
                service.base_price = form.base_price.data
                service.time_required = form.time_required.data
                flash('Service updated successfully!', 'success')
            else:
                # Add a new service
                new_service = Service(
                    service_type=form.service_type.data,
                    service_description=form.service_description.data,
                    base_price=form.base_price.data,
                    time_required = form.time_required.data
                )
                db.session.add(new_service)
                flash('New service added successfully!', 'success')

            db.session.commit()
            return redirect(url_for('adminhome'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing the service.', 'danger')

    #populate the form if editing
    if service:
        form.service_type.data = service.service_type
        form.service_description.data = service.service_description
        form.base_price.data = service.base_price
        form.time_required.data = service.time_required

    return render_template('addnewservice.html', form=form, service=service)



@app.route('/adminsummary')
def adminsummary():
    tpr = len(ServiceRequest.query.filter_by(service_status='Pending').all())
    tcr = len(ServiceRequest.query.filter_by(service_status='Completed').all())
    tor = len(ServiceRequest.query.filter_by(service_status='Open').all())
    query_result = (db.session.query(Professional, Service.base_price, func.coalesce(func.avg(ServiceReview.ratings), 0).label('avg_rating')).join(Service, Professional.service_type == Service.service_type).outerjoin(ServiceRequest, and_(Professional.id == ServiceRequest.professional_id,ServiceRequest.service_status != 'rejected')).outerjoin(ServiceReview, ServiceRequest.id == ServiceReview.service_request_id).group_by(Professional, Service.base_price).all())
    return render_template('adminsummary.html',title='Admin-Summary',show_navbar=True,tpr=tpr,tcr=tcr,tor=tor,query_result=query_result)

@app.route('/customersummary')
@login_required
def customersummary():
    id = current_user.customer_id
    tpr = len(ServiceRequest.query.filter_by(customer_id = id,service_status='Pending').all())
    tcr = len(ServiceRequest.query.filter_by(customer_id = id,service_status='Completed').all())
    tor = len(ServiceRequest.query.filter_by(customer_id = id,service_status='Open').all())
    
    return render_template('customersummary.html',title='Customer-Summary',show_navbar=True,tpr=tpr,tcr=tcr,tor=tor)

@app.route('/professionalsummary')
@login_required
def professionalsummary():
    id = current_user.professional_id
    tpr = len(ServiceRequest.query.filter_by(professional_id = id,service_status='Pending').all())
    tcr = len(ServiceRequest.query.filter_by(professional_id = id,service_status='Completed').all())
    tor = len(ServiceRequest.query.filter_by(professional_id = id,service_status='Open').all())
    query_result = (db.session.query(Professional, Service.base_price, func.coalesce(func.avg(ServiceReview.ratings), 0).label('avg_rating')).join(Service, Professional.service_type == Service.service_type).outerjoin(ServiceRequest, and_(Professional.id == ServiceRequest.professional_id,ServiceRequest.service_status != 'rejected')).outerjoin(ServiceReview, ServiceRequest.id == ServiceReview.service_request_id).group_by(Professional, Service.base_price).all())
    for a,_,c in query_result:
        if a.email == current_user.email :
            avg_rating = c
    return render_template('professionalsummary.html',title='Professional-Summary',show_navbar=True,tpr=tpr,tcr=tcr,tor=tor,avg_rating=avg_rating)

@app.route('/ratings')
@app.route('/ratings/<int:service_request_id>/<int:professional_id>', methods=['GET', 'POST'])
def ratings(service_request_id, professional_id):
    form = Ratings()
    servicerequestdetails = ServiceRequest.query.filter_by(id = service_request_id).first()
    if form.validate_on_submit():
        servicereview = ServiceReview(remarks=form.service_remarks.data,ratings=form.service_ratings.data,service_request_id=service_request_id)
        db.session.add(servicereview)
        db.session.commit()
        flash('Thank you for HouseKarting','info')
        return redirect(url_for('customerhome'))
    return render_template('ratings.html',title='Ratings',show_navbar=True,servicerequestdetails=servicerequestdetails,form=form)


@app.route('/profdoc/<string:email>',methods=["GET","POST"])
def profdoc(email):
    try:
        filename = f'{email}.pdf'
        # Serve the file from the uploads folder
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        abort(404)  # Return 404 if the file does not exist


@app.route('/adminservicedetails/<int:id>',methods=['GET','POST'])
def adminservicedetails(id):
    service = Service.query.get(id)
    action2 = request.form.get('action2')
    # Edit/Delete Service
    if action2:
        if action2 == 'edit':
            return redirect(url_for('addservice', service_id=id))
        elif action2 == 'delete':
            delete_service = Service.query.get(id)
            if delete_service:
                try:
                    db.session.delete(delete_service)
                    db.session.commit()
                    flash('Service deleted successfully!', 'success')
                    return redirect(url_for('adminhome'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while deleting the service.', 'danger')
            else:
                flash('Service not found. Unable to delete.', 'danger')
    return render_template('adminservicedetails.html',title='Service details',show_navbar=True,service = service)

@app.route('/adminprofessionaldetails/<int:id>',methods=['GET','POST'])
def adminprofessionaldetails(id):
    action3 = request.form.get('blockprof')
    unblock_professional = request.form.get('unblockprof')
    professional_approval = request.form.get("profapproval")
    professionals = Professional.query.get(id)
     # Block Professional
    if action3 == 'blockprof':
        block_prof = Professional.query.filter_by(id=id).first()
        if not block_prof.is_blocked:
            block_prof.is_blocked = True
            db.session.commit()
            flash(f'Professional {block_prof.full_name} was blocked successfully', 'warning')
        else:
            flash('This Professional was already blocked', 'danger')
        return redirect(url_for('adminhome'))
    
    # Unblock Professional
    if unblock_professional == 'unblockprof':
        unblock_prof = Professional.query.filter_by(id=id).first()
        if  unblock_prof.is_blocked:
            unblock_prof.is_blocked = False
            db.session.commit()
            flash(f'Professional {unblock_prof.full_name} was unblocked successfully', 'success')
        else:
            flash('This Professional is already unblocked', 'info')
        return redirect(url_for('adminhome'))


    # Approve/Reject Professional
    if professional_approval:
        if professional_approval == 'approve':
            approve_prof = Professional.query.filter_by(id=id).first()
            if approve_prof:
                approve_prof.is_approved = True
                db.session.commit()
                flash(f'Professional {approve_prof.full_name} approved successfully', 'success')
            else:
                flash("Professional not found. Cannot approve.", 'danger')
        elif professional_approval == 'reject':
            rejected_prof = Professional.query.filter_by(id=id).first()
            if rejected_prof:
                db.session.delete(rejected_prof)
                db.session.commit()
                flash(f"Professional {rejected_prof.full_name}'s application was rejected", 'info')
            else:
                flash("Professional not found. Cannot reject application.", 'danger')
        return redirect(url_for('adminhome'))
    return render_template('adminprofessionaldetails.html',title='Professional details',show_navbar=True,professional=professionals)

@app.route('/admincustomerdetails/<int:id>',methods=['GET','POST'])
def admincustomerdetails(id):
    customer = Customer.query.get(id)
    block_customer = request.form.get('blockcustomer')
    unblock_customer = request.form.get('unblockcustomer')
    #Block Customer
    if block_customer == 'blockcustomer':
        block_cust = Customer.query.filter_by(id = id).first()
        block_cust.is_blocked = True
        db.session.commit()
        flash(f'Customer {block_cust.full_name} was blocked','danger')
        return redirect(url_for('adminhome'))
    
    #Unblock Customer 
    if unblock_customer == 'unblockcustomer':
        unblock_cust = Customer.query.filter_by(id = id).first()
        unblock_cust.is_blocked = False
        db.session.commit()
        flash(f'Customer {unblock_cust.full_name} was unblocked','success')
        return redirect(url_for('adminhome'))
    return render_template('admincustomerdetails.html',title='Customer details',show_navbar=True,customer=customer)

@app.route('/adminservicerequestdetails/<int:id>',methods=['GET','POST'])
def adminservicerequestdetails(id):
    sr=ServiceRequest.query.get(id)
    return render_template('adminservicerequestdetails.html',title='Service request details',service_request=sr,show_navbar=True)

@app.route('/customeredit/<int:cust_id>/<int:user_id>',methods=['GET','POST'])
def customeredit(cust_id,user_id):
    customer=Customer.query.get(cust_id)
    user=User.query.get(user_id)
    form=CustomerUpdateForm()
    if form.validate_on_submit():
        try:
            if customer and user:
                customer.email=form.email.data
                customer.full_name=form.full_name.data
                customer.contact=form.contact.data
                customer.address=form.address.data
                customer.pincode=form.pincode.data

                user.email=form.email.data
                user.full_name=form.full_name.data
                user.contact=form.contact.data


            else:
                pass
            db.session.commit()


           
            flash(f'Account details updated!','success')
            return redirect(url_for('customerhome'))
        # if customer already exist
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing the service.', 'danger')
    if customer:
        form.email.data = customer.email
        form.full_name.data = customer.full_name
        form.contact.data = customer.contact
        form.address.data = customer.address
        form.pincode.data = customer.pincode

    return render_template('customeredit.html',show_navbar=True,title='Customer-Edit',form=form)

@app.route('/professionaledit/<int:prof_id>/<int:user_id>',methods=['GET','POST'])
def professionaledit(prof_id,user_id):
    professional=Professional.query.get(prof_id)
    user=User.query.get(user_id)
    form=ProfessionalUpdateForm()
    if form.validate_on_submit():
        try:
            if professional and user:
                professional.email=form.email.data
                professional.full_name=form.full_name.data
                professional.contact=form.contact.data
                professional.service_description=form.service_description.data
                professional.address=form.address.data
                professional.pincode=form.pincode.data

                user.email=form.email.data
                user.full_name=form.full_name.data
                user.contact=form.contact.data

            else:
                pass
            db.session.commit()


           
            flash(f'Account details updated!','success')
            return redirect(url_for('professionalhome'))
        # if customer already exist
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing the service.', 'danger')
    if professional:
        form.email.data = professional.email
        form.full_name.data = professional.full_name
        form.contact.data = professional.contact
        form.service_description.data=professional.service_description
        form.address.data = professional.address
        form.pincode.data = professional.pincode

    return render_template('professionaledit.html',show_navbar=True,title='Professional-Edit',form=form)

if __name__ == '__main__':
    app.run(debug=True)
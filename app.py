from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skelp.db'
db = SQLAlchemy()
migrate = Migrate(app, db)
db.init_app(app)


class Balance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)


@app.route('/', methods=['GET', 'POST'])
def index():
    if Balance.query.all():
        saldo = Balance.query.first()
    else:
        balance = Balance(balance=0)
        db.session.add(balance)
        db.session.commit()
    products = Product.query.all()

    request.method == 'POST'
    zmiana_saldo = request.form.get('zmiana_saldo')
    if zmiana_saldo:
        zmiana_saldo = float(zmiana_saldo)

        if zmiana_saldo < 0 and abs(zmiana_saldo) > saldo.balance:
            return "Nie można wypłacić więcej niż wynosi aktualne saldo"
        else:
            saldo.balance = max(0, saldo.balance + zmiana_saldo)
            db.session.add(saldo)
            db.session.commit()

            if zmiana_saldo < 0:
                balance_text = f"Wypłacono {zmiana_saldo} PLN"
            else:
                balance_text = f"Wpłacono {zmiana_saldo} PLN"

            history_entry = History(text=balance_text)
            db.session.add(history_entry)
            db.session.commit()

        return redirect(url_for('index'))

    return render_template('index.html', stan_konta=saldo.balance, stan_magazynu=products)


@app.route('/zakup', methods=['POST'])
def formularz_zakupu():
    nazwa_produktu = request.form['nazwa_produktu']
    cena = float(request.form['cena'])
    ilosc = int(request.form['ilosc'])

    total_cost = cena * ilosc

    if Balance.query.all():
        saldo = Balance.query.first()
        if saldo.balance < total_cost:
            return "Brak wystarczających środków na zakup."

        saldo.balance = max(0, saldo.balance - total_cost)
        db.session.add(saldo)
        db.session.commit()

    existing_product = Product.query.filter_by(name=nazwa_produktu).first()

    if existing_product:
        existing_product.quantity += ilosc
    else:
        product = Product(
            name=nazwa_produktu,
            price=cena,
            quantity=ilosc
        )
        db.session.add(product)
    db.session.commit()
    purchase_text = f"Zakupiono {nazwa_produktu} w ilości {ilosc} za cenę {total_cost} PLN"

    existing_history_entry = History.query.filter_by(text=purchase_text).first()
    if not existing_history_entry:
        history_entry = History(text=purchase_text)
        db.session.add(history_entry)
        db.session.commit()

    return redirect(url_for('index'))


@app.route('/sprzedaz', methods=['POST'])
def formularz_sprzedazy():
    nazwa_produktu = request.form['nazwa_produktu']
    cena = float(request.form['cena'])
    ilosc = int(request.form['ilosc'])

    total_cost = cena * ilosc

    product = Product.query.filter_by(name=nazwa_produktu).first()

    if product and product.quantity >= ilosc:
        product.quantity -= ilosc
        db.session.add(product)
        db.session.commit()

        saldo = Balance.query.first()
        saldo.balance += total_cost
        db.session.add(saldo)
        db.session.commit()

        if product.quantity == 0:
            db.session.delete(product)
            db.session.commit()

        sale_text = f"Sprzedano {ilosc} sztuk {nazwa_produktu} za cenę {total_cost} PLN"
        existing_history_entry = History.query.filter_by(text=sale_text).first()

        if not existing_history_entry:
            history_entry = History(text=sale_text)
            db.session.add(history_entry)
            db.session.commit()

    else:
        return "Nie wystarczająca ilość produktu na stanie lub produkt nie istnieje w magazynie."

    return redirect(url_for('index'))


@app.route('/historia/')
def history():
        history = History.query.all()
        return render_template('historia.html', history=history, total_entries=len(history))


if __name__ == "__main__":
    app.run(debug=True)
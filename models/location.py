from . import db

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    barangay = db.Column(db.String(100), nullable=False)
    municipality = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)

    # Changed from backref to back_populates to match Student model
    students = db.relationship('Student', back_populates='location')

    def to_dict(self):
        return{
            'id': self.id,
            'barangay': self.barangay,
            'municipality': self.municipality,
            'province': self.province
        }
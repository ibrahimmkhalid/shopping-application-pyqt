class UserData():
    def __init__(self, user_id, email, name, street, city, state, zip_code, date_of_birth, gender, is_admin=False):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.is_admin = is_admin

    def get_formatted_address(self):
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;
use validator::ValidateEmail;

const MAX_USERNAME_LENGTH: usize = 50;

#[derive(Clone, Copy, Default, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum UserRole {
    #[default]
    Student,
    Admin,
}

#[derive(Clone, Serialize)]
pub(crate) struct User {
    id: usize,
    username: String,
    email: String,
    role: UserRole,
}

#[derive(Deserialize)]
pub(crate) struct UserCreate {
    username: String,
    email: String,
    #[serde(default)]
    role: UserRole,
}

pub(crate) enum UserError {
    Invalid(&'static str),
    Duplicate,
}

#[derive(Default)]
pub(crate) struct UserService {
    users: RwLock<Vec<User>>,
}

impl UserService {
    pub(crate) async fn add_user(&self, payload: UserCreate) -> Result<User, UserError> {
        let username = payload.username.trim().to_owned();
        let email = payload.email.trim().to_lowercase();
        if !(1..=MAX_USERNAME_LENGTH).contains(&username.chars().count()) {
            return Err(UserError::Invalid(
                "O nome de usuário deve ter entre 1 e 50 caracteres",
            ));
        }
        if !email.validate_email() {
            return Err(UserError::Invalid("E-mail inválido"));
        }

        let mut users = self.users.write().await;
        if users
            .iter()
            .any(|user| unicase::eq(&user.username, &username) || unicase::eq(&user.email, &email))
        {
            return Err(UserError::Duplicate);
        }
        let user = User {
            id: users.len() + 1,
            username,
            email,
            role: payload.role,
        };
        users.push(user.clone());
        Ok(user)
    }

    pub(crate) async fn list_users(&self) -> Vec<User> {
        self.users.read().await.clone()
    }
}

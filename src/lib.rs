use std::sync::Arc;

use axum::{
    Json, Router,
    extract::{OriginalUri, State, rejection::JsonRejection},
    http::StatusCode,
    response::{IntoResponse, Redirect, Response},
    routing::get,
};
use serde::Serialize;

mod users;
use users::{User, UserCreate, UserError, UserService};

enum ApiError {
    Json(JsonRejection),
    User(UserError),
}

#[derive(Serialize)]
struct ErrorBody {
    detail: String,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, detail) = match self {
            Self::Json(error) => (StatusCode::UNPROCESSABLE_ENTITY, error.body_text()),
            Self::User(UserError::Invalid(detail)) => {
                (StatusCode::UNPROCESSABLE_ENTITY, detail.to_owned())
            }
            Self::User(UserError::Duplicate) => (
                StatusCode::CONFLICT,
                "Usuário ou e-mail já cadastrado".to_owned(),
            ),
        };
        (status, Json(ErrorBody { detail })).into_response()
    }
}

pub fn router() -> Router {
    Router::new()
        .route("/users/", get(list_users).post(create_user))
        .route("/users", get(redirect_users).post(redirect_users))
        .with_state(Arc::new(UserService::default()))
}

async fn redirect_users(OriginalUri(uri): OriginalUri) -> Redirect {
    let location = match uri.query() {
        Some(query) => format!("/users/?{query}"),
        None => "/users/".to_owned(),
    };
    Redirect::temporary(&location)
}

async fn list_users(State(service): State<Arc<UserService>>) -> Json<Vec<User>> {
    Json(service.list_users().await)
}

async fn create_user(
    State(service): State<Arc<UserService>>,
    payload: Result<Json<UserCreate>, JsonRejection>,
) -> Result<(StatusCode, Json<User>), ApiError> {
    let Json(payload) = payload.map_err(ApiError::Json)?;
    let user = service.add_user(payload).await.map_err(ApiError::User)?;
    Ok((StatusCode::CREATED, Json(user)))
}

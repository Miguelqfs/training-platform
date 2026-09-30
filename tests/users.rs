use axum::{
    Router,
    body::{Body, to_bytes},
    http::{Request, StatusCode},
    response::Response,
};
use serde_json::{Value, json};
use tower::ServiceExt;

async fn post(app: Router, payload: Value) -> Response {
    app.oneshot(
        Request::post("/users/")
            .header("content-type", "application/json")
            .body(Body::from(payload.to_string()))
            .unwrap(),
    )
    .await
    .unwrap()
}

async fn body(response: Response) -> Value {
    let bytes = to_bytes(response.into_body(), 1024 * 1024).await.unwrap();
    serde_json::from_slice(&bytes).unwrap()
}

async fn list(app: Router) -> Value {
    let response = app
        .oneshot(Request::get("/users/").body(Body::empty()).unwrap())
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::OK);
    body(response).await
}

#[tokio::test]
async fn deve_criar_e_listar_usuarios_em_ordem() {
    let app = training_platform::router();
    assert_eq!(list(app.clone()).await, json!([]));
    for (id, username) in [(1, "davi"), (2, "ana")] {
        let response = post(
            app.clone(),
            json!({"username": format!(" {username} "), "email": format!(" {}@EXAMPLE.COM ", username.to_uppercase())}),
        )
        .await;
        assert_eq!(response.status(), StatusCode::CREATED);
        assert_eq!(
            body(response).await,
            json!({"id": id, "username": username, "email": format!("{username}@example.com"), "role": "student"})
        );
    }
    assert_eq!(
        list(app).await,
        json!([
            {"id": 1, "username": "davi", "email": "davi@example.com", "role": "student"},
            {"id": 2, "username": "ana", "email": "ana@example.com", "role": "student"}
        ])
    );
}

#[tokio::test]
async fn deve_rejeitar_nome_ou_email_duplicado_sem_consumir_id() {
    let app = training_platform::router();
    post(
        app.clone(),
        json!({"username": "davi", "email": "davi@example.com"}),
    )
    .await;
    for payload in [
        json!({"username": " DAVI ", "email": "outro@example.com", "role": "admin"}),
        json!({"username": "outro", "email": " DAVI@EXAMPLE.COM ", "role": "admin"}),
    ] {
        let response = post(app.clone(), payload).await;
        assert_eq!(response.status(), StatusCode::CONFLICT);
        assert_eq!(
            body(response).await,
            json!({"detail": "Usuário ou e-mail já cadastrado"})
        );
    }
    let response = post(
        app.clone(),
        json!({"username": "ana", "email": "ana@example.com"}),
    )
    .await;
    assert_eq!(body(response).await["id"], 2);
    assert_eq!(list(app).await.as_array().unwrap().len(), 2);
}

#[tokio::test]
async fn deve_rejeitar_entradas_invalidas_sem_alterar_a_lista() {
    let app = training_platform::router();
    for payload in [
        json!({"username": "", "email": "davi@example.com"}),
        json!({"username": "   ", "email": "davi@example.com"}),
        json!({"username": "é".repeat(51), "email": "davi@example.com"}),
        json!({"username": "davi", "email": "invalido"}),
        json!({"username": "davi"}),
        json!({"username": 123, "email": "davi@example.com"}),
    ] {
        let response = post(app.clone(), payload).await;
        assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
        assert!(body(response).await["detail"].is_string());
    }
    assert_eq!(list(app).await, json!([]));
}

#[tokio::test]
async fn deve_criar_e_listar_alunos_e_administradores() {
    let app = training_platform::router();
    for role in ["student", "admin"] {
        let response = post(
            app.clone(),
            json!({
                "username": role, "email": format!("{role}@example.com"), "role": role
            }),
        )
        .await;
        assert_eq!(response.status(), StatusCode::CREATED);
        assert_eq!(body(response).await["role"], role);
    }
    assert_eq!(
        list(app).await,
        json!([
            {"id": 1, "username": "student", "email": "student@example.com", "role": "student"},
            {"id": 2, "username": "admin", "email": "admin@example.com", "role": "admin"}
        ])
    );
}

#[tokio::test]
async fn deve_rejeitar_papeis_invalidos_sem_cadastrar_usuario() {
    let app = training_platform::router();
    for role in [json!("trainer"), json!("ADMIN"), json!(null), json!(1)] {
        let response = post(
            app.clone(),
            json!({
                "username": "ana", "email": "ana@example.com", "role": role
            }),
        )
        .await;
        assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
    }
    assert_eq!(list(app).await, json!([]));
}

#[tokio::test]
async fn deve_comparar_duplicatas_com_case_folding_unicode() {
    let app = training_platform::router();
    let response = post(
        app.clone(),
        json!({
            "username": "Straße", "email": "davi@example.com"
        }),
    )
    .await;
    assert_eq!(response.status(), StatusCode::CREATED);
    let response = post(
        app.clone(),
        json!({
            "username": " STRASSE ", "email": "ana@example.com"
        }),
    )
    .await;
    assert_eq!(response.status(), StatusCode::CONFLICT);
}

#[tokio::test]
async fn deve_isolar_a_colecao_por_instancia_da_aplicacao() {
    let app = training_platform::router();
    post(
        app.clone(),
        json!({"username": "davi", "email": "davi@example.com"}),
    )
    .await;
    assert_eq!(list(training_platform::router()).await, json!([]));
    assert_eq!(list(app).await.as_array().unwrap().len(), 1);
}

#[tokio::test]
async fn deve_contar_caracteres_unicode_em_vez_de_bytes() {
    let response = post(
        training_platform::router(),
        json!({"username": format!(" {} ", "é".repeat(50)), "email": "davi@example.com"}),
    )
    .await;
    assert_eq!(response.status(), StatusCode::CREATED);
}

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
async fn deve_permitir_apenas_um_cadastro_duplicado_concorrente() {
    let app = training_platform::router();
    let barrier = std::sync::Arc::new(tokio::sync::Barrier::new(16));
    let mut tasks = tokio::task::JoinSet::new();
    for _ in 0..16 {
        let app = app.clone();
        let barrier = barrier.clone();
        tasks.spawn(async move {
            barrier.wait().await;
            post(
                app,
                json!({"username": "davi", "email": "davi@example.com"}),
            )
            .await
            .status()
        });
    }
    let mut created = 0;
    while let Some(result) = tasks.join_next().await {
        match result.unwrap() {
            StatusCode::CREATED => created += 1,
            StatusCode::CONFLICT => {}
            status => panic!("Status inesperado: {status}"),
        }
    }
    assert_eq!(created, 1);
    assert_eq!(list(app).await.as_array().unwrap().len(), 1);
}

#[tokio::test]
async fn deve_retornar_json_para_corpo_malformado() {
    let response = training_platform::router()
        .oneshot(
            Request::post("/users/")
                .header("content-type", "application/json")
                .body(Body::from("{"))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
    assert!(body(response).await["detail"].is_string());
}

#[tokio::test]
async fn deve_redirecionar_preservando_o_metodo() {
    for method in ["GET", "POST"] {
        for (uri, location) in [
            ("/users", "/users/"),
            ("/users?source=mobile", "/users/?source=mobile"),
        ] {
            let response = training_platform::router()
                .oneshot(
                    Request::builder()
                        .method(method)
                        .uri(uri)
                        .body(Body::empty())
                        .unwrap(),
                )
                .await
                .unwrap();
            assert_eq!(response.status(), StatusCode::TEMPORARY_REDIRECT);
            assert_eq!(response.headers()["location"], location);
        }
    }
}

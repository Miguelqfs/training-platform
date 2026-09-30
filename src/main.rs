use std::{env, error::Error, future::Future, io};

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let address = env::var("BIND_ADDRESS").unwrap_or_else(|_| "127.0.0.1:8000".to_owned());
    let listener = tokio::net::TcpListener::bind(&address).await?;
    let shutdown = shutdown_signal()?;
    println!("Users API em http://{}", listener.local_addr()?);
    axum::serve(listener, training_platform::router())
        .with_graceful_shutdown(shutdown)
        .await?;
    Ok(())
}

fn shutdown_signal() -> io::Result<impl Future<Output = ()>> {
    #[cfg(unix)]
    let mut terminate = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())?;

    Ok(async move {
        let ctrl_c = async {
            if let Err(error) = tokio::signal::ctrl_c().await {
                eprintln!("Não foi possível aguardar Ctrl+C: {error}");
            }
        };

        #[cfg(unix)]
        let terminate = async move {
            terminate.recv().await;
        };
        #[cfg(not(unix))]
        let terminate = std::future::pending::<()>();

        tokio::select! {
            _ = ctrl_c => {},
            _ = terminate => {},
        }
    })
}

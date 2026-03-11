from app import create_app

app = create_app()

if __name__ == '__main__':
    # host='0.0.0.0' tells the app to listen on all public IPs.
    app.run(host='0.0.0.0', port=5013, debug=True)
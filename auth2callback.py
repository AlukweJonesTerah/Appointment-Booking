# @app.route('/oauth2callback')
# def oauth2callback():
#     try:
#         flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
#         flow.redirect_uri = url_for('oauth2callback', _external=True)
#
#         # Use the authorization response to fetch the tokens
#         authorization_response = request.url
#         flow.fetch_token(authorization_response=authorization_response)
#
#         # Obtain the credentials
#         credentials = flow.credentials
#
#         # Save the obtained token to the user's model
#         if current_user.is_authenticated:
#             current_user.set_google_calendar_token(credentials.to_json())
#
#         # Write the token to a local file
#         with open("token.json", "w") as token_file:
#             token_file.write(credentials.to_json())
#
#         return redirect('/success')  # Redirect to a success page
#
#     except Exception as e:
#         # Handle exceptions and log errors
#         return f'Error: {str(e)}'
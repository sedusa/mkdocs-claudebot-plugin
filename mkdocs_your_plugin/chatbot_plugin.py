import os
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from anthropic import Client

class ChatbotPlugin(BasePlugin):
    config_scheme = (
        ('api_key', config_options.Type(str, required=True)),
        ('model', config_options.Type(str, default='claude-v1')),
        ('temperature', config_options.Type(float, default=0.5)),
        ('max_tokens', config_options.Type(int, default=100)),
    )

    def on_post_build(self, config):
        api_key = self.config['api_key']
        model = self.config['model']
        temperature = self.config['temperature']
        max_tokens = self.config['max_tokens']

        client = Client(api_key)

        def generate_response(query):
            response = client.completion(
                prompt=f"{query}\n\nAssistant:",
                model=model,
                max_tokens_to_sample=max_tokens,
                temperature=temperature,
            )
            return response.completion.content

        chatbot_html = '''
        <div id="chatbot-container">
            <div id="chatbot-header">ChatBot</div>
            <div id="chatbot-messages"></div>
            <input type="text" id="chatbot-input" placeholder="Type your message...">
            <button id="chatbot-send">Send</button>
        </div>
        '''

        chatbot_css = '''
        #chatbot-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            height: 400px;
            background-color: #f1f1f1;
            border: 1px solid #ccc;
            border-radius: 5px;
            display: flex;
            flex-direction: column;
        }
        #chatbot-header {
            background-color: #333;
            color: white;
            padding: 10px;
            font-weight: bold;
        }
        #chatbot-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        #chatbot-input {
            padding: 10px;
            border: none;
            border-top: 1px solid #ccc;
        }
        #chatbot-send {
            padding: 10px;
            background-color: #333;
            color: white;
            border: none;
            cursor: pointer;
        }
        '''

        chatbot_js = '''
        <script>
            function sendMessage() {
                var input = document.getElementById('chatbot-input');
                var message = input.value.trim();
                if (message !== '') {
                    var messagesDiv = document.getElementById('chatbot-messages');
                    messagesDiv.innerHTML += '<p><strong>You:</strong> ' + message + '</p>';
                    input.value = '';

                    fetch('/chatbot', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ message: message })
                    })
                    .then(response => response.json())
                    .then(data => {
                        var assistantResponse = data.response;
                        messagesDiv.innerHTML += '<p><strong>Assistant:</strong> ' + assistantResponse + '</p>';
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    });
                }
            }

            document.getElementById('chatbot-send').addEventListener('click', sendMessage);
            document.getElementById('chatbot-input').addEventListener('keyup', function(event) {
                if (event.keyCode === 13) {
                    sendMessage();
                }
            });
        </script>
        '''

        extra_css = os.path.join(config['site_dir'], 'assets', 'css', 'chatbot.css')
        with open(extra_css, 'w') as f:
            f.write(chatbot_css)

        extra_js = os.path.join(config['site_dir'], 'assets', 'js', 'chatbot.js')
        with open(extra_js, 'w') as f:
            f.write(chatbot_js)

        for page in config['pages']:
            if page.endswith('.html'):
                page_path = os.path.join(config['site_dir'], page)
                with open(page_path, 'r+') as f:
                    content = f.read()
                    if '</body>' in content:
                        content = content.replace('</body>', chatbot_html + '</body>')
                        f.seek(0)
                        f.write(content)
                        f.truncate()

    def on_serve(self, server, config, builder):
        @server.app.route('/chatbot', methods=['POST'])
        def chatbot():
            data = server.app.request.get_json()
            message = data['message']
            response = generate_response(message)
            return server.app.response_class(
                response=json.dumps({'response': response}),
                status=200,
                mimetype='application/json'
            )
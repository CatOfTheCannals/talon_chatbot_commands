import requests
import json
import os
from typing import Optional
from talon import Module, actions, keychain

# TODO: Make it only available to run one request at a time

mod = Module()
mod.setting(
    "open_ai_fixup_prompt",
    type=str,
    default="Fix any grammar, ponctuation, and typos.",
    desc="Prompt to use when using GPT to fix misrecognitions.",
)
# Make sure you at your openai api key to talon's keychain through talon's REPL
# keychain.add('OPENAI_API_KEY', '', 'OpenAI API Key')
TOKEN = keychain.find('OPENAI_API_KEY', '')


def gpt_query(prompt: str, content: str) -> Optional[str]:
    headers = {
        'Content-Type': 'application/json',
        
        'Authorization': f'Bearer {TOKEN}'
    }

    data = {
        'messages': [{'role': 'user', 'content': f"{prompt}:\n{content}"}],
        'max_tokens': 2024,
        'temperature': 0.6,
        'n': 1,
        'stop': None,
        'model': 'gpt-3.5-turbo'
    }

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()

    return None

def gpt_task(prompt: str, content: str, task_name: str) -> str:
    """Run a GPT task"""
    actions.app.notify(f"GPT: Task ({task_name}) started")
    resp = gpt_query(prompt, content)

    if not resp:
        actions.app.notify('GPT: Something went wrong...')
        return None

    actions.app.notify('GPT: Task ({task_name}) finished')
    return resp


class BaseChatbotTask:
    def __init__(self):
        self.prompt = None
        self.task_name = None

    def ask_chatbot(self):
            content = actions.edit.selected_text()
            resp = gpt_task(self.prompt, content, self.task_name)

            if resp:
                actions.user.paste(resp)


class BaseTranscriptionInterpreter(BaseChatbotTask):  
    def __init__(self):
        self.task_name = None
        self.specific_task_description = None  
        self.generic_transcription_prompt = """
            I'm using voice recognition software for dictation. 
            Please interpret the input text by assuming \
                some words or sequences of words are actually misrecognitions from the ASR. 
            Pay special attention both to homophones and to expressions that sound similar. 
            Fix any grammar, punctuation, and typos. 
            Use a friendly tone and text message style.
            Some examples:
            - towards / to words
            - light / like
            - capricious / couple issues
            - guest / gist
            - green / bring
            - rubber / wrapper
            - The cut is under day's tail. -> the cat is under the table
            """
        
    @property
    def prompt(self):
        return self.generic_transcription_prompt + self.specific_task_description
        

class TranscriptionGrammarFixer(BaseTranscriptionInterpreter):  

    def __init__(self):
        super().__init__()
        self.task_name = 'grammar_fixer'
        self.specific_task_description = """
            Your job is to only return a meaningful interpretation \
                of the input provided below
            """


class TranscriptionSpanishTranslator(BaseTranscriptionInterpreter):  

    def __init__(self):
        super().__init__()
        self.task_name = 'translate_spanish'
        self.specific_task_description = """
            Your job is to only return a meaningful porteño spanish translation \
                of the input provided below
            """
            

class TranscriptionMailConverter(BaseTranscriptionInterpreter):  

    def __init__(self):
        super().__init__()
        self.task_name = 'mail_converter'
        self.specific_task_description = """
            Your job is to Interpret the information provided below \
            and only provide an email based it  
            """


class FrenchTutorialCreator(BaseChatbotTask):

    def __init__(self):
        self.task_name = 'french_tutorial'
        self.prompt = """
            Given the provided french text below your job is to \
            split it in lines and translate every one of them porteño spanish.
            Make sure their arrangement follows the next pattern:
            - french sentence number one.
            - translated sentence number one.
            
            - french sentence number two.
            - translated sentence number two.
            
            For example, if giving the text \
            "Le chat est sous la table. Le chat est noir." \
            Then you should write:
            - Le chat est sous la table.
            - El gato está bajo la mesa.
            
            - Le chat est noir.
            - El gato es negro.

            Now perform the translation given the following french text:
            """


@mod.action_class
class Actions:
    def fix_grammar():
        """Fix grammar, punctuation, and typos."""
        TranscriptionGrammarFixer().ask_chatbot()

    def translate_spanish():
        """Translate to porteño spanish."""
        TranscriptionSpanishTranslator().ask_chatbot()

    def convert_to_mail():
        """Convert to mail."""
        TranscriptionMailConverter().ask_chatbot()

    def french_tutorial():
        """Translate french text to porteño spanish \
            in a sentence by sentence fashion."""
        FrenchTutorialCreator().ask_chatbot()
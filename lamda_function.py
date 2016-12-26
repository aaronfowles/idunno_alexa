"""
"""

from __future__ import print_function
import requests

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {"stage": 0}
    res = requests.get('https://idunno.io/api/get_questions')
    questions = res.json()['questions']
    session_attributes['questions'] = list(questions)
    session_attributes['tags'] = {}
    session_attributes['yes_list'] = []
    session_attributes['no_list'] = []
    question_object = session_attributes['questions'][session_attributes['stage']]
    question = question_object['question_text']
    card_title = "Welcome to iDunno. "
    speech_output = "Welcome to iDunno. Would you like to {}? ".format(question)
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Sooooo. "
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "See ya! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def answer_question(intent, session):
    """
    """
    session_attributes = session['attributes']
    stage = session['attributes']['stage']
    if 'response' in intent['slots']:
        answer = intent['slots']['response']['value']
        tag = session['attributes']['questions'][stage]['tag_name']
        session['attributes']['tags'][tag] = answer
        if 'response'== 'yes':
            session['attributes']['yes_list'] = session['attributes']['questions'][stage]['id']
        elif 'response' == 'no':
            session['attributes']['no_list'] = session['attributes']['questions'][stage]['id']
    session['attributes']['stage'] += 1
    new_stage = session['attributes']['stage']
    card_title = intent['name']
    should_end_session = False
    if new_stage < 5:
        question_object = session_attributes['questions'][new_stage]
        question = question_object['question_text']
        speech_output = "Would you like to {}? ".format(question)
        reprompt_text = speech_output
    else:
        payload = {'yes_list': session['attributes']['yes_list'], 'no_list': session['attributes']['no_list']}
        res = requests.get('https://idunno.io/api/get_activities', params=payload)
        decision = res.json()['activity_description']
        speech_output = "iDunno thinks you should {}? ".format(decision)
        reprompt_text = speech_output
        should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "answerQuestion":
        return answer_question(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

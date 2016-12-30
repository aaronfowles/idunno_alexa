"""
"""

from __future__ import print_function
import requests

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    if title is not None:
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
                },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }
    else:
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


# --------------- Functions that control the skill's behavior -----------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {"stage": 0}
    res = requests.get('https://idunno.io/api/get_questions')
    questions = res.json()['questions']
    session_attributes['questions'] = list(questions)
    session_attributes['yes_list'] = []
    session_attributes['no_list'] = []
    question_object = session_attributes['questions'][session_attributes['stage']]
    question = question_object['question_text']
    card_title = None
    speech_output = "Let's find something for you to do. Would you like to {}? ".format(question)
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = speech_output
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def answer_question(intent, session):
    """
    """
    session_attributes = session['attributes']
    stage = session['attributes']['stage']
    if 'response' in intent['slots']:
        answer = intent['slots']['response']['value']
        if answer == 'yes':
            session['attributes']['yes_list'].append(session['attributes']['questions'][stage]['id'])
        elif answer == 'no':
            session['attributes']['no_list'].append(session['attributes']['questions'][stage]['id'])
    session['attributes']['stage'] += 1
    new_stage = session['attributes']['stage']
    card_title = None
    should_end_session = False
    if new_stage < 5:
        question_object = session_attributes['questions'][new_stage]
        question = question_object['question_text']
        speech_output = "Would you like to {}? ".format(question)
        reprompt_text = speech_output
    else:
        yes_list = str(session['attributes']['yes_list'])
        no_list = str(session['attributes']['no_list'])
        payload = {'yes_list': yes_list, 'no_list': no_list}
        res = requests.get('https://idunno.io/api/alexa_get_activities', params=payload)
        decision = res.json()['activity_desc']
        speech_output = "iDunno thinks you should {}. ".format(decision)
        reprompt_text = speech_output
        should_end_session = True
        card_title = "iDunno says..."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_help(intent, session):
    card_title = "How to use iDunno"
    session_attributes = session['attributes']
    should_end_session = False

    speech_output = "Just open the skill and answer the five questions to hear a suggestion from iDunno. "
    reprompt_text = speech_output
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def exit_skill(intent, session):
    card_title = None
    session_attributes = session['attributes']
    should_end_session = True

    speech_output = ""
    reprompt_text = speech_output

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------


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
    if intent_name == "mapToWelcome":
        return get_welcome_response()
    if intent_name == "AMAZON.HelpIntent":
        return get_help(intent, session)
    if intent_name == "AMAZON.StopIntent":
        return exit_skill(intent, session)
    if intent_name == "AMAZON.CancelIntent":
        return exit_skill(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here
    card_title = "Session Ended"
    speech_output = "See ya! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


# --------------- Main handler ------------------


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

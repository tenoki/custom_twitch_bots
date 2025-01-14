##Setup python to read from Twitch IRC server.
import platform     #For getting the OS name
import re           #For regular expression
import socket       #For connection
import subprocess   #For accessing the system's shell environment

##Setup python to use the Google Text-to-Speech System
from gtts import gTTS   #Either import this with pip or install using your 
                        #distribution's package manager. 
from io import BytesIO
#import playsound       #Could not get this to work in a cross platform 
                        #compatible way for now.


#Info used to connect to Twitch IRC Server
server   = 'irc.chat.twitch.tv'
port     = 6667
nickname = 'mastic_warrior'
channel  = '#mastic_warrior'

#Read Twitch OAuth Token from file. --- Protect Your Secrets! ---
oauth = open("oauth.token", "r")
token = oauth.read()
oauth.close()

#Variables for the gTTS engines.
tld  = "co.in"
tlds = ["English (Australia)       : en    : com.au", 
        "English (United Kingdom)  : en    : co.uk", 
        "English (United States)   : en    : com",
        "English (Canada)          : en    : ca",
        "English (India)           : en    : co.in",
        "English (Ireland)         : en    : ie",
        "English (South Africa)    : en    : co.za",
        "English (Nigeria)         : en    : com.ng",
        "French (Canada)           : fr    : ca",
        "French (France)           : fr    : fr",
        "Mandarin (China Mainland) : zh-CN : any",
        "Mandarin (Taiwan)         : zh-TW : any",
        "Portuguese (Brazil)       : pt    : com.br",
        "Portuguese (Portugal)     : pt    : pt",
        "Spanish (Mexico)          : es    : com.mx",
        "Spanish (Spain)           : es    : es",
        "Spanish (United States)   : es    : com"    ]
language = "en"

#Variables for Flow Control
stopReceived = False

#Regular Expression Variables
regex_username_search = ':(.*)\\!.*\\@'
regex_usermessage_search = ':[\\w]*![\\w]*@[\\w]*\\W[\\w]*\\W[\\w]*\\W\\w\\w\\sPRIVMSG\\s#[\\w]*\\s:([\\w\\W]*)'


#Creating a socket to connect to Twitch IRC Relay
chat_socket = socket.socket()
#Connect to the Twitch IRC Server
chat_socket.connect((server, port))
#Authenticate with the Twitch IRC Server
chat_socket.send(f"PASS {token}\n".encode('utf-8'))
chat_socket.send(f"NICK {nickname}\n".encode('utf-8'))
chat_socket.send(f"JOIN {channel}\n".encode('utf-8'))


#Consume initial server messages.
chat_response = chat_socket.recv(2048).decode('utf-8')
print(chat_response)
chat_response = chat_socket.recv(2048).decode('utf-8')
print(chat_response)


#Keep the session open until the !tts_stop command has been received.
while (stopReceived == False) : 
    print("Waiting for next message from chat...")
    #Grab the current response in the server list.
    chat_response = chat_socket.recv(4096).decode('utf-8')
    print('Message Received:\n\t' + repr(chat_response) )
  
    #Tokenize the response from the server.
    response_tokens = chat_response.split("\r\n")
    print("\tTokens: " + str( len(response_tokens) ))

    #Handle command cases.
    for response in response_tokens :
        print("\tResponse from server: " + repr(response))
        
        #If the message is a PING from Twitch's IRC Server
        if  "PING" in response :
            chat_socket.send( "PONG\n".encode('utf-8') ) #Send a PONG response 
                                                     #to keep the socket 
                                                     #open.
            print('PONG response sent to server.\n')
        #Chat issues the stop command.
        elif "!tts stop" in response :
            print('\tTTS Stop command received!\n')
            stopRecieved = True
            chat_socket.close() #Close the socket.
            print('\n')
            exit() #End the program.
        #Chat issues the change language command.
        elif "!tts language" in response :
            language = str( re.search('[\\w\\W]*:!tts language ([\\w]*)', chat_response).group(1) )
            print('\tLanguage set to', language, '\n')
        #Chat issues the change accent command.
        elif "!tts tld" in response :
            tld = str( re.search('[\\w\\W]*:!tts tld\\s([\\w,\\.]*)', chat_response).group(1) )
            print( '\tAccent set to ' + tld, "\n" )
        #Chat issues the list languages command.
        elif "!tts list languages" in response :
            result = subprocess.run("gtts-cli list --all" , shell = True, capture_output = True, check = True, text = True)
            print('\tSending list of languages to the chat:\n' + str(result.stdout), '\n')
        #Chat issues the list accents command.
        elif "!tts list tlds" in response :
            print( '\tAvailable TLDs:' )
            for accent in tlds :
                print( "\t\t" + accent )
            print('\n')
        elif len(response) == 0:
                break
        #Capture each chat message and feed to TTS.
        else :
            #Use a regular expression to get the user name and their message.
            username     = re.search(':(.*)\\!.*\\@', response).group(1)
            user_message = re.search(':[\\w]*![\\w]*@[\\w]*\\W[\\w]*\\W[\\w]*\\W\\w\\w\\sPRIVMSG\\s#[\\w]*\\s:([\\w\\W]*)', response).group(1)
            user_message = user_message.replace("\"", "\'")
            #Generate text to feed to gTTS
            tts_text = "User " + str(username) + " says, " + str(user_message)

            #Determine OS as the command will be different between GNU/Linux 
            #and MS Windows due to environment variables and permissions.
            if platform.system().startswith('Windows') :
                #Import more MS Windows specifics
                import win32com.client as wincom
                #Initials the MS Windows TTS Engine
                spvoice_tts = wincom.Dispatch("SAPI.SpVoice")
                #Build the command string for debug.
                tts_command = "spvoice_tts.Speak(\"" + tts_text + "\")"
                print( "\tTTS Command: ", tts_command)
                #Run the command. May only work on MS Windows 10 and 11 systems.
                spvoice_tts.Speak(tts_text)
            # End Handle MS Windows if.
            elif platform.system().startswith('Linux'):
                #Configure the gTTS command to execute text to speech.
                #Build the command.
                gtts_command = "gtts-cli --lang \"" + str(language) \
                             + "\" --tld \"" + str(tld) + "\" \"" \
                             + tts_text + "\" | paplay"
                print( 'TTS Command: ' )
                print("\t", gtts_command, flush=True )
                #Run the command in the system shell interpreter.
                subprocess.run(gtts_command , shell = True, check = True, text = True)
            #End handle GNU/Linux if.

            print("End conversion of chat message.\n") # Carriage return to separate the next input.
        #End send text to TTS if
#End while loop

#Close the socket
chat_socket.close()

# MIT License

# Copyright (c) 2020 Anshuman Pattnaik

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import argparse
import json
import time
import os
import sys
import re
from termcolor import colored
from lib.Utils import Utils
from lib.Constants import Constants
from lib.SocketConnection import SocketConnection
from pathlib import Path
import colorama

colorama.init()

utils = Utils()
constants = Constants()

# Argument parser
parser = argparse.ArgumentParser(description='HTTP Request Smuggling vulnerability detection tool')
parser.add_argument("-u", "--url", help="set the target url")
parser.add_argument("-urls", "--urls", help="set list of target urls, i.e (urls.txt)")
parser.add_argument("-t", "--timeout", help="set socket timeout, default - 10")
parser.add_argument("-w", "--wait", type=float, default=0.1, help="set each waiting time (seconds), default - 1")
parser.add_argument("-m", "--method", help="set HTTP Methods, i.e (GET or POST), default - POST")
args = parser.parse_args()

history_value = [None, None, None]
original_value = None

def get_original_status_code(_host, _port, _path, _method, _timeout, waiting_time):
    global original_value
    headers = ''
    headers += '{} {} HTTP/1.1{}'.format(_method, _path, constants.crlf)
    headers += 'Host: {}{}'.format(_host, constants.crlf)
    smuggle_body = headers + "\r\n\r\n"

    permute_type = "[Origin]"
    elapsed_time = "-"

    # Print Styling
    _style_space_config = "{:<30}{:<25}{:<25}{:<25}{:<25}"
    _style_permute_type = colored("[Origin]", constants.cyan, attrs=['bold'])
    _style_smuggle_type = colored("raw", constants.magenta, attrs=['bold'])
    _style_status_code = colored("-", constants.blue, attrs=['bold'])
    _style_elapsed_time = "{}".format(colored(elapsed_time, constants.yellow, attrs=['bold']))
    _style_status = colored(constants.detecting, constants.green, attrs=['bold'])
    smuggle_type = "raw"

    print(_style_space_config.format(_style_permute_type, _style_smuggle_type, _style_status_code, _style_elapsed_time,
                                     _style_status), end="\r", flush=True)

    start_time = time.time()
    status_code = 0

    try:
        connection = SocketConnection()
        connection.connect(_host, _port, _timeout)
        connection.send_payload(smuggle_body)

        response = connection.receive_data().decode("utf-8")
        end_time = time.time()

        if len(response.split()) > 0:
            status_code = response.split()[1]
        else:
            status_code = 'NO RESPONSE'
        _style_status_code = colored(status_code, constants.blue, attrs=['bold'])

        connection.close_connection()

        # The detection logic is based on the time delay technique, if the elapsed time is more than the timeout value
        # then the target host status will change to [HRS → Vulnerable], but most of the time chances are it can be
        # false positive So to confirm the vulnerability you can use burp-suite turbo intruder and try your own
        # payloads. https://portswigger.net/web-security/request-smuggling/finding

        elapsed_time = str(round((end_time - start_time) % 60, 2)) + "s"
        _style_elapsed_time = "{}".format(colored(elapsed_time, constants.yellow, attrs=['bold']))

        is_hrs_found = connection.detect_hrs_vulnerability(start_time, _timeout)

        # If HRS found then it will write the payload to the reports directory
        if is_hrs_found:
            _style_status = colored(constants.delayed_response_msg, constants.red, attrs=['bold'])
            _reports = constants.reports + '/{}/{}-{}{}'.format(_host, permute_type, smuggle_type, constants.extenstion)
            utils.write_payload(_reports, smuggle_body)

        elif history_value[0] == permute_type and history_value[1] == smuggle_type and history_value[2] != status_code:
            _style_status = colored(constants.status_code_no_match, constants.red, attrs=['bold'])
        else:
            _style_status = colored(constants.ok, constants.green, attrs=['bold'])

    except Exception as exception:
        elapsed_time = str(round((time.time() - start_time) % 60, 2)) + "s"
        _style_elapsed_time = "{}".format(colored(elapsed_time, constants.yellow, attrs=['bold']))

        error = f'{constants.dis_connected} → {exception}'
        _style_status = colored(error, constants.red, attrs=['bold'])

    print(_style_space_config.format(_style_permute_type, _style_smuggle_type, _style_status_code, _style_elapsed_time,
                                         _style_status))

    # There is a delay of 1 second after executing each payload
    time.sleep(waiting_time)

    original_value = status_code

def hrs_detection(_host, _port, _path, _method, permute_type, content_length_key, te_key, te_value, smuggle_type,
                  content_length, payload, _timeout, waiting_time, original = False):
    global history_value
    global original_value
    headers = ''
    headers += '{} {} HTTP/1.1{}'.format(_method, _path, constants.crlf)
    headers += 'Host: {}{}'.format(_host, constants.crlf)
    smuggle_body = headers + "\r\n\r\n"

    if not original :
        headers += '{} {}{}'.format(content_length_key, content_length, constants.crlf)
        headers += '{}{}{}'.format(te_key, te_value, constants.crlf)
        smuggle_body = headers + payload

    #print(smuggle_body)
    permute_type = "[" + permute_type + "]"
    elapsed_time = "-"

    # Print Styling
    _style_space_config = "{:<30}{:<25}{:<25}{:<25}{:<25}"
    if original:
        _style_permute_type = colored("[Origin]", constants.cyan, attrs=['bold'])
        _style_smuggle_type = colored("raw", constants.magenta, attrs=['bold'])
    else:
        _style_permute_type = colored(permute_type, constants.cyan, attrs=['bold'])
        _style_smuggle_type = colored(smuggle_type, constants.magenta, attrs=['bold'])
    _style_status_code = colored("-", constants.blue, attrs=['bold'])
    _style_elapsed_time = "{}".format(colored(elapsed_time, constants.yellow, attrs=['bold']))
    _style_status = colored(constants.detecting, constants.green, attrs=['bold'])

    print(_style_space_config.format(_style_permute_type, _style_smuggle_type, _style_status_code, _style_elapsed_time,
                                     _style_status), end="\r", flush=True)

    start_time = time.time()
    status_code = 0

    try:
        connection = SocketConnection()
        connection.connect(_host, _port, _timeout)
        connection.send_payload(smuggle_body)

        response = connection.receive_data().decode("utf-8")
        end_time = time.time()

        if len(response.split()) > 0:
            status_code = response.split()[1]
        else:
            status_code = 'NO RESPONSE'
        _style_status_code = colored(status_code, constants.blue, attrs=['bold'])

        connection.close_connection()

        # The detection logic is based on the time delay technique, if the elapsed time is more than the timeout value
        # then the target host status will change to [HRS → Vulnerable], but most of the time chances are it can be
        # false positive So to confirm the vulnerability you can use burp-suite turbo intruder and try your own
        # payloads. https://portswigger.net/web-security/request-smuggling/finding

        elapsed_time = str(round((end_time - start_time) % 60, 2)) + "s"
        _style_elapsed_time = "{}".format(colored(elapsed_time, constants.yellow, attrs=['bold']))

        is_hrs_found = connection.detect_hrs_vulnerability(start_time, _timeout)

        # If HRS found then it will write the payload to the reports directory
        if is_hrs_found:
            _style_status = colored(constants.delayed_response_msg, constants.red, attrs=['bold'])
            _reports = constants.reports + '/{}/{}-{}{}'.format(_host, permute_type, smuggle_type, constants.extenstion)
            utils.write_payload(_reports, smuggle_body)

        elif history_value[0] == permute_type and history_value[1] == smuggle_type and history_value[2] != status_code and not original:
            _style_status = colored(constants.status_code_no_match, constants.red, attrs=['bold'])
        elif original_value != status_code and original:
            _style_status = colored(constants.status_code_no_match, constants.red, attrs=['bold'])
        else:
            _style_status = colored(constants.ok, constants.green, attrs=['bold'])

    except Exception as exception:
        elapsed_time = str(round((time.time() - start_time) % 60, 2)) + "s"
        _style_elapsed_time = "{}".format(colored(elapsed_time, constants.yellow, attrs=['bold']))

        error = f'{constants.dis_connected} → {exception}'
        _style_status = colored(error, constants.red, attrs=['bold'])

    print(_style_space_config.format(_style_permute_type, _style_smuggle_type, _style_status_code, _style_elapsed_time,
                                         _style_status))

    # There is a delay of 1 second after executing each payload
    time.sleep(waiting_time)

    if not original:
        history_value[0] = permute_type
        history_value[1] = smuggle_type
        history_value[2] = status_code

if __name__ == "__main__":
    # If the python version less than 3.x then it will exit
    if sys.version_info < (3, 0):
        print(constants.python_version_error_msg)
        sys.exit(1)

    try:
        # Printing the tool header
        utils.print_header()

        # Both (url/urls) options not allowed at the same time
        if args.urls and args.url:
            print(constants.invalid_url_options)
            sys.exit(1)

        target_urls = list()
        if args.urls:
            urls = utils.read_target_list(args.urls)

            if constants.file_not_found in urls:
                print(f"[{args.urls}] not found in your local directory")
                sys.exit(1)
            target_urls = urls

        if args.url:
            target_urls.append(args.url)

        for url in target_urls:
            result = utils.url_parser(url)
            try:
                json_res = json.loads(result)
                host = json_res['host']
                port = json_res['port']
                path = json_res['path']

                # If host is invalid then it will exit
                if host is None:
                    print(f"Invalid host - {host}")
                    sys.exit(1)

                method = args.method.upper() if args.method else "POST"
                pattern = re.compile('GET|POST')
                if not (pattern.match(method)):
                    print(constants.invalid_method_type)
                    sys.exit(1)

                timeout = int(args.timeout) if args.timeout else 10

                square_left_sign = colored('[', constants.cyan, attrs=['bold'])
                plus_sign = colored("+", constants.green, attrs=['bold'])
                square_right_sign = colored(']', constants.cyan, attrs=['bold'])
                square_sign = "{}{}{:<16}".format(square_left_sign, plus_sign, square_right_sign)

                retry = 1

                target_header_style_config = '{:<1}{}{:<25}{:<16}{:<10}'
                print(target_header_style_config.format('', square_sign,
                                                        colored("Target URL", constants.magenta, attrs=['bold']),
                                                        colored(":", constants.magenta, attrs=['bold']),
                                                        colored(url, constants.blue, attrs=['bold'])))
                print(target_header_style_config.format('', square_sign,
                                                        colored("Method", constants.magenta, attrs=['bold']),
                                                        colored(":", constants.magenta, attrs=['bold']),
                                                        colored(method, constants.blue, attrs=['bold'])))
                print(target_header_style_config.format('', square_sign,
                                                        colored("Retry", constants.magenta, attrs=['bold']),
                                                        colored(":", constants.magenta, attrs=['bold']),
                                                        colored(retry, constants.blue, attrs=['bold'])))
                print(target_header_style_config.format('', square_sign,
                                                        colored("Timeout", constants.magenta, attrs=['bold']),
                                                        colored(":", constants.magenta, attrs=['bold']),
                                                        colored(timeout, constants.blue, attrs=['bold'])))

                reports = os.path.join(str(Path().absolute()), constants.reports, host)
                print(target_header_style_config.format('', square_sign,
                                                        colored("HRS Reports", constants.magenta, attrs=['bold']),
                                                        colored(":", constants.magenta, attrs=['bold']),
                                                        colored(reports, constants.blue, attrs=['bold'])))
                print()

                script_dir = os.path.dirname(os.path.abspath(__file__))
                payloads_path = os.path.join(script_dir, 'payloads.json')
                payloads = open(payloads_path)
                data = json.load(payloads)

                payload_list = list()

                get_original_status_code(host, port, path, method, timeout, args.wait)

                for permute in data[constants.permute]:
                    for d in data[constants.detection]:
                        # Based on the retry value it will re-execute the same payload again
                        transfer_encoding_obj = permute[constants.transfer_encoding]
                        for _ in range(3):
                            hrs_detection(host, port, path, method, permute[constants.type],
                                          permute[constants.content_length_key],
                                          transfer_encoding_obj[constants.te_key],
                                          transfer_encoding_obj[constants.te_value],
                                          d[constants.type],
                                          d[constants.content_length],
                                          d[constants.payload],
                                          timeout, args.wait, original=False)
                        hrs_detection(host, port, path, method, permute[constants.type],
                                      permute[constants.content_length_key],
                                      transfer_encoding_obj[constants.te_key],
                                      transfer_encoding_obj[constants.te_value],
                                      d[constants.type],
                                      d[constants.content_length],
                                      d[constants.payload],
                                      timeout, args.wait, original=True)
            except ValueError as _:
                print(result)
    except KeyboardInterrupt as e:
        print(e)

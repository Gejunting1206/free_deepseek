from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import time
import uuid

app = FastAPI()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import html2text
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 定义OpenAI兼容的请求/响应模型
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    # 其他参数...


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]


# 模拟的模型生成函数
def mock_generate_response(messages: List[ChatMessage], model) -> str:
    def wait_ai_response(driver):
        ai_response_text = WebDriverWait(driver, 1000000).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ds-markdown.ds-markdown--block"))
        ).get_attribute("innerHTML")
        ai_response_text_old = ''
        stop_time = 0
        while True:
            if stop_time > 8:
                break
            if ai_response_text != ai_response_text_old:
                stop_time += 1
            else:
                stop_time = 0
                ai_response_text_old = ai_response_text
                ai_response_text = WebDriverWait(driver, 1000000).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.ds-markdown.ds-markdown--block"))
                ).get_attribute("innerHTML")

            time.sleep(1)

    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://chat.deepseek.com")

    tabs_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ds-tabs.ds-tabs--line.ds-sign-up-form__tabs"))
    )

    # 2. 定位 "密码登录" tab 元素 (可以通过多种方式定位)

    # 方式 1: 通过文本内容定位 (XPath) (推荐，如果文本内容稳定)
    password_login_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ds-tab:nth-child(2)"))
    )

    password_login_tab.click()

    username = WebDriverWait(driver, 100000000).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input.ds-input__input[type='text'][placeholder='请输入手机号/邮箱地址']"))  # 根据实际元素修改
    )
    username.send_keys("15942826206")

    # 填写密码
    password = WebDriverWait(driver, 100000000).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input.ds-input__input[type='password'][placeholder='请输入密码']"))  # 根据实际元素修改
    )
    password.send_keys("junting1206")

    is_read = WebDriverWait(driver, 100000000).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ds-checkbox"))  # 根据实际元素修改
    )
    is_read.click()

    sign_in = WebDriverWait(driver, 100000000).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ds-sign-up-form__register-button"))  # 根据实际元素修改
    )
    sign_in.click()

    if 'r1' in model:
        print("使用推理模型")
        button = WebDriverWait(driver, 100000).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'ds-button') and contains(., '深度思考 (R1)')]"))
        )
        button.click()

    element = WebDriverWait(driver, 100000000).until(
        EC.presence_of_element_located((By.ID, "chat-input"))
    )

    # ai_input = driver.find_element("id", "chat-input")
    element.send_keys(messages[-1].content)

    send_button = WebDriverWait(driver, 100000000).until(
        EC.presence_of_element_located((By.CLASS_NAME, "f6d670"))
    )
    send_button.click()
    wait_ai_response(driver)
    ai_response_element = WebDriverWait(driver, 1000000).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ds-markdown.ds-markdown--block"))
    )
    ai_response_text = ai_response_element.get_attribute("innerHTML")

    driver.quit()

    return html2text.html2text(ai_response_text)


@app.post("/v1/chat/completions")
async def chat_completion(
        request: ChatCompletionRequest,
        authorization: str = Header(None)
):
    # 验证API密钥（可选）
    if authorization != "Bearer your-api-key":
        raise HTTPException(status_code=401, detail="Invalid authorization")

    # 生成回复
    response_content = mock_generate_response(request.messages, request.model)

    # 构建兼容响应
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        created=int(time.time()),
        model=request.model,
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }
        ]
    )


# 错误处理
@app.exception_handler(HTTPException)
async def openai_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "invalid_request_error",
                "code": exc.status_code
            }
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
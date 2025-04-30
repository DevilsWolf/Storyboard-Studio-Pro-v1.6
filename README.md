# Storyboard-Studio-Pro-v1.6

Read carefully ....... 

ok i want to tell you this code is 99 percent is ai generated code . Its just a prototype whats possible in python only my goal was to make a storyboard app like ltx studio or atleast get a idea how to do it if anyone wants to 
do it in locally . For this program to work you need two things one is Lm studio and other one is fooocus api . both i will tell you how to install . i will provide link and everything how i did it . This is a basic gui app .
To run this app you need to install fooocus api .

Clone the fooocus-api repo (git clone https://github.com/mrhan1993/Fooocus-API.git)
inside the cloned folder create a new virtual environment and activate it
For virtual environment run this : (python -m venv .venv;)
to activate the environment run this : (.venv\Scripts\activate)
install the requirements.txt (pip install -r requirements.txt)
if you already have Fooocus installed on your machine, go to the Fooocus folder and look for the config.txt file. Copy this file and paste it into the root folder of Fooocus-API
run Fooocus-API (inside the Fooocus-API root folder run python main.py)
go to http://localhost:8888/docs to see the swagger specification of the API


ok this is for image generation it will directly load into your vram . I have faced many problem for memory management i didnt find a decent solution for it so i did the next best thing . i have 32 gb ram and 8gb nvidia 
4060 . So spcifically run lm studion and go to their api section and set the model manually load into ram not vram . Vram ofloading i set to zero so for that whenever my program call llm to write the script it will automatically load into ram and whwenever it calls fooocus api it run on vram . Hence no memory problem . 

![Screenshot_127](https://github.com/user-attachments/assets/7c5962af-3f0b-4046-9f46-e6fa4fc06786)


And a successful api connenction to the fooocus will look like the screenshot . 

![Screenshot_128](https://github.com/user-attachments/assets/9ac8e2c2-bc4e-44c4-bd9e-f713ffe62bda)



And to run this program just git clone this repo and go inside and run in your terminal python main.py thats it . if you set those things carefully mentioned above it will run . 
You might want to install this (pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118). Because its neccesary for fooocus to use your vram . otherwise it might gives you error . 
So to sum it up you need to run lm studio and start the server with any model but remember if you use any other model than mine in the first screenshot you have to mention into the config.ini . otherwise it might not work . 
And if you want to use any other sdxl model you might want to change the model name into config.ini . So this is it for the most of the part . My python version is 3.12.10 So for optimze performance you can install it . 
I know its a very minor steps to go . But trust me its a good way to forward . people can modify it further or you can make this idea into a full stack web app which i will do next if i get the time . this whole app was built within 30 hours . you can see by version how many changes it went through . I meant i was frustrated a lot during the coding session because it was giving silly errors which took long to fix . So if anyone interested to expand on this idea you are free to do it . 



Here are some screenshot in action and its potential 

![Screenshot_123](https://github.com/user-attachments/assets/3b6f3095-c9e3-4040-80b5-b9b750c2649a)
![Screenshot_124](https://github.com/user-attachments/assets/73f2afc5-e063-47a8-bf2e-316a6b6a60d6)
![Screenshot_125](https://github.com/user-attachments/assets/d0018ead-5232-4466-836e-52031974f29d)
![Screenshot_126](https://github.com/user-attachments/assets/2a536bcf-f7c9-4650-b8bf-c80e80b15bc0)




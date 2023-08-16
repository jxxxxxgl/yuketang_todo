package main

import (
	"bytes"
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"os"
	"os/exec"
	"time"
)

func main() {
	ginServer := gin.Default()
	// 加载静态页面
	ginServer.LoadHTMLGlob("templates/*")

	ginServer.GET("/", func(c *gin.Context) {
		c.HTML(http.StatusOK, "index.html", nil)
	})

	ginServer.POST("/yun", func(c *gin.Context) {
		username := c.PostForm("username")
		password := c.PostForm("password")
		dropdown := c.PostForm("dropdown")
		url := c.PostForm("url")
		fmt.Println(username, password, dropdown, url)
		cmd := exec.Command("python3", "yun.py", "-U", username, "-P", password, "-M", dropdown, "-C", url)
		currentTime := time.Now()

		fmt.Println("用户" + username + "密码" + password + "在" + currentTime.String() + "使用脚本")

		var out bytes.Buffer
		var stderr bytes.Buffer
		cmd.Stdout = &out
		cmd.Stderr = &stderr

		err := cmd.Run()
		if err != nil {
			fmt.Println(fmt.Sprint(err) + ": " + stderr.String())
			return
		}
		fmt.Println("Result: " + out.String())

		output1, _ := cmd.Output()
		fmt.Println("运行python脚本输出：%s", string(output1))

		err = cmd.Start()

		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	})
	ginServer.Run("0.0.0.0:8082")
}

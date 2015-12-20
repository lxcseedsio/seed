package main

import (
        "fmt"
        "log"

        "gopkg.in/yaml.v2"
        "io/ioutil"
)

var data, err = ioutil.ReadFile("./seed.yml")
/*var data = `
a: Easy!
b:
  c: 2
  d: [3, 4]
`*/


type Repository struct   {
  Remote string
  Alias string
}

type Config struct   {
  Description string
  Source Repository
  Destination Repository
  Exec string
  Alias string
}

func main() {
var config Config
        err = yaml.Unmarshal([]byte(data), &config)
        if err != nil {
                log.Fatalf("error: %v", err)
        }
        fmt.Printf("--- m:\n%#v\n\n", config)
}

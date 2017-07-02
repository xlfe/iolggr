(defproject iolggr-frontend "0.1.0"
            :description "iolggr first OmNext"
            :dependencies [
                           [org.clojure/clojure "1.8.0"]
                           [org.clojure/clojurescript "1.9.562"]
                           [com.stuartsierra/component "0.3.2"]
                           [org.omcljs/om "1.0.0-beta1" :exclusions [cljsjs/react cljsjs/react-dom]]
                           [cljs-react-material-ui "0.2.45"]
                           [figwheel-sidecar "0.5.4-7" :scope "test"]
                           ]
  )
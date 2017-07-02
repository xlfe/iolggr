(ns iolggr.core
  (:require
    [cljsjs.material-ui]
    [cljs-react-material-ui.core :as ui]
    [cljs-react-material-ui.icons :as ic]
    [goog.dom :as gdom]
    [cljs.core.async :as async :refer [<! >! put! chan]]
    [clojure.string :as string]
    [om.next :as om :refer-macros [defui]]
    [om.dom :as dom])
  (:require-macros [cljs.core.async.macros :refer [go]])
  (:import [goog Uri]
           [goog.net Jsonp]))


(defui Chart
  Object
  (render [this]
    (dom/div nil "chart"))
  (componentDidMount [this]
    ;    (p/catch #(js/alert (str "Unable to parse spec:\n\n" %)))
    ;    (p/then #(-> (% {:el (dom/node this)})
    ;                 (.update))))
    ))

(enable-console-print!)

(def init-data
  {:list/one [{:name "John" :points 0}
              {:name "Mary" :points 0}
              {:name "Bob" :points 0}]
   :list/two [{:name "Mary" :points 0 :age 27}
              {:name "Gwen" :points 0}
              {:name "Jeff" :points 0}]})

;; -----------------------------------------------------------------------------
;; Parsing

;         name dispatch-fn
(defmulti read om/dispatch)

(defn get-people [state key]
  (let [st @state]
    (into [] (map #(get-in st %)) (get st key))))

; read function must return a hashmap containing a :value entry
(defmethod read :list/one
  ; the signature of a read fn is [env key params] - env is a hash map containing context & key is the requested key
  ; destructuring state from env
  [{:keys [state] :as env} key params]
  {:value (get-people state key)})

(defmethod read :list/two
  [{:keys [state] :as env} key params]
  {:value (get-people state key)})

(defmulti mutate om/dispatch)

; mutations return :action (function with no arguments)
; :value is the a hashmap with :keys communicates what read operations should follow a mutation
(defmethod mutate 'points/increment
  [{:keys [state]} _ {:keys [name]}]
  {:action
   (fn []
     (swap! state update-in
            [:person/by-name name :points]
            inc))})

(defmethod mutate 'points/decrement
  [{:keys [state]} _ {:keys [name]}]
  {:action
   (fn []
     (swap! state update-in
            [:person/by-name name :points]
            #(let [n (dec %)] (if (neg? n) 0 n))))})

;; -----------------------------------------------------------------------------
;; Components

(defui Person
  static om/Ident
  (ident [this {:keys [name]}]
    [:person/by-name name])
  static om/IQuery
  (query [this]
    '[:name :points :age])
  Object
  (render [this]
    (let [{:keys [points name] :as props} (om/props this)]
      (ui/list-item
        (dom/label nil (str name ", points: " points))
        (dom/button
          #js {:onClick
               (fn [e]
                 (om/transact! this
                               `[(points/increment ~props)]))}
          "+")
        (dom/button
          #js {:onClick
               (fn [e]
                 (om/transact! this
                               `[(points/decrement ~props)]))}
          "-")))

    )
  )
;https://micahasmith.github.io/2015/10/19/clojurescript-is-easy/
;https://stackoverflow.com/questions/34810803/how-do-i-use-google-charts-in-clojurescript-with-om

(def person (om/factory Person {:keyfn :name}))

(defui ListView
  Object
  (render [this]
    (let [list (om/props this)]
      (apply ui/list
             (map person list)))))

(def list-view (om/factory ListView))

(def sensors [
              {:name "Laundry"}
              {:name "Hallway"}
              {:name "Study"}
              ]
  )


(defui RootView
  Object
  (render [this]
    (let [{:keys [list/one list/two]} (om/props this)]
      (ui/mui-theme-provider
        {:mui-theme (ui/get-mui-theme)}
        (dom/div
          #js {:className "h-100"}
          (ui/app-bar
            {:title "iolggr"})
          (ui/drawer
             {:open true
             :docked false
             :onRequestChange (fn [e] (print e) (.setState this {:open e}))
             }
            (ui/list
              (ui/list-item 1)
              (ui/list-item 1)
              (ui/list-item 1)
              (map #(ui/list-item (get % :name)) sensors))



      ))))))


(def reconciler
  (om/reconciler
    {:state  init-data
     :parser (om/parser {:read read :mutate mutate})}))

(om/add-root! reconciler
              RootView (gdom/getElement "app"))

